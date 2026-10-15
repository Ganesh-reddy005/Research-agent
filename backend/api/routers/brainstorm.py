import json
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage
from api.models import BrainstormRequest
from utils.auth import get_current_user, get_supabase_client, verify_session, ensure_profile

router = APIRouter(prefix="/api/research/brainstorm", tags=["research"])

@router.post("")
async def brainstorm_research(request: BrainstormRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.brainstorm_graph
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    if request.chat_id:
        chat_id = request.chat_id
        await verify_session(chat_id, user.id)
    else:
        # New conversation: record it so it shows up in the user's history
        chat_id = str(uuid.uuid4())
        supabase = get_supabase_client()
        try:
            await ensure_profile(user)
            await asyncio.to_thread(supabase.table("sessions").insert({
                "thread_id": chat_id,
                "user_id": user.id,
                "topic": message[:120],
                "research_mode": "brainstorm",
                "status": "active"
            }).execute)
        except Exception as e:
            print(f"Failed to record brainstorm: {e}")
            raise HTTPException(status_code=500, detail="Could not save this conversation")

    config = {"configurable": {"thread_id": chat_id}}

    def thought(token):
        return {"event": "thought", "data": json.dumps({"agent": "brainstorm", "token": token, "thread_id": chat_id})}

    async def event_generator():
        streamed, model_run = False, None
        try:
            async for event in graph.astream_events({"messages": [HumanMessage(content=message)]}, config=config, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream" and event["metadata"].get("langgraph_node") == "agent":
                    token = event["data"]["chunk"].content
                    if isinstance(token, str) and token:
                        if streamed and event["run_id"] != model_run:
                            yield thought("\n\n")  # text from a new model call starts a new paragraph
                        model_run = event["run_id"]
                        streamed = True
                        yield thought(token)
                elif kind == "on_custom_event" and event["name"] in ("search_start", "search_end"):
                    # Live "Searching arXiv for ..." progress and the sources found
                    yield {"event": event["name"], "data": json.dumps(event["data"])}
            if not streamed:
                # Provider didn't stream tokens; send the saved reply in one piece
                snapshot = await graph.aget_state(config)
                yield thought(snapshot.values["messages"][-1].content)
            yield {"event": "done", "data": json.dumps({"status": "completed", "thread_id": chat_id})}
        except Exception as e:
            print(f"Brainstorm Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator(), ping=20)

@router.get("/{chat_id}")
async def get_brainstorm(chat_id: str, req: Request, user=Depends(get_current_user)):
    """Saved messages of a brainstorm conversation."""
    await verify_session(chat_id, user.id)
    snapshot = await req.app.state.brainstorm_graph.aget_state({"configurable": {"thread_id": chat_id}})
    return {"chat_id": chat_id, "messages": to_chat_messages((snapshot.values or {}).get("messages", []))}

def to_chat_messages(messages):
    """One assistant message per user turn, carrying the searches that turn ran."""
    out, parts, searches = [], [], []
    for m in messages:
        if m.type == "human":
            out.append({"role": "user", "content": m.content})
            parts, searches = [], []
        elif m.type == "tool":
            artifact = m.artifact or {}
            searches.append({"id": m.tool_call_id, "tool": artifact.get("tool", m.name), "query": artifact.get("query", ""),
                             "status": "done", "sources": artifact.get("sources", [])})
        elif m.type == "ai":
            if isinstance(m.content, str) and m.content:
                parts.append(m.content)
            if not m.tool_calls:  # the turn's final answer
                out.append({"role": "assistant", "content": "\n\n".join(parts), "searches": searches})
    return out
