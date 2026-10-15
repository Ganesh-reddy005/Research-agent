import json
import uuid
import asyncio
from fastapi import APIRouter, Request, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from api.models import ResearchStartRequest, ResearchResumeRequest
from utils.auth import get_current_user, get_supabase_client, verify_session, ensure_profile

router = APIRouter(prefix="/api/research", tags=["research"])

# State fields the dashboard needs to restore a session
SESSION_FIELDS = [
    "topic", "research_mode", "clarification_questions", "user_answers", "research_brief",
    "research_plan", "raw_sources", "assistance_summary", "draft_report", "final_report",
    "citation_audit_log", "current_step",
]

# Agents whose LLM output is prose worth showing live; the rest emit JSON
STREAMED_AGENTS = {"assistance", "synthesis", "writer", "critic", "refinement"}

async def stream_graph(graph, graph_input, config, thread_id, on_complete=None):
    """SSE events for one graph run: agent starts, progress, live prose, finished steps,
    then where it paused (interrupt) or that it finished (done)."""
    def event(name, **data):
        return {"event": name, "data": json.dumps({"thread_id": thread_id, **data})}

    try:
        async for ev in graph.astream_events(graph_input, config=config, version="v2"):
            kind, node = ev["event"], ev["metadata"].get("langgraph_node")

            if kind == "on_chain_start" and node and ev["name"] == node:
                yield event("agent_start", agent=node)
            elif kind == "on_custom_event" and ev["name"] == "progress":
                yield event("progress", agent=node, message=ev["data"].get("message", ""))
            elif kind == "on_chat_model_stream" and node in STREAMED_AGENTS:
                content = ev["data"]["chunk"].content
                if isinstance(content, str) and content:
                    yield event("thought", agent=node, token=content)
            elif kind == "on_chain_end" and node and ev["name"] == node:
                output = ev["data"].get("output")
                if output and isinstance(output, dict):
                    yield event("step", step=node, state=output)

        snapshot = await graph.aget_state(config)
        if snapshot.next:
            yield event("interrupt", next=snapshot.next)
        else:
            if on_complete:
                await on_complete()
            yield event("done", status="completed")
    except Exception as e:
        print(f"SSE Error: {e}")
        yield {"event": "error", "data": json.dumps({"error": str(e)})}

@router.post("/start")
async def start_research(request: ResearchStartRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.graph
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Record session in Supabase
    supabase = get_supabase_client()
    try:
        await ensure_profile(user)
        await asyncio.to_thread(supabase.table("sessions").insert({
            "thread_id": thread_id,
            "user_id": user.id,
            "topic": request.topic,
            "research_mode": request.mode or "deep",
            "status": "active"
        }).execute)
    except Exception as e:
        print(f"Failed to record session: {e}")
        raise HTTPException(status_code=500, detail="Could not initialize research session in database")

    state = {
        "topic": request.topic,
        "research_mode": request.mode or "deep",
        "thread_id": thread_id,
        "user_id": str(user.id)
    }
    return EventSourceResponse(stream_graph(graph, state, config, thread_id), ping=20)

@router.post("/resume")
async def resume_research(request: ResearchResumeRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.graph
    await verify_session(request.thread_id, user.id)
    
    config = {"configurable": {"thread_id": request.thread_id}}
    data = request.data or {}
    
    if request.action == "answer":
        await graph.aupdate_state(config, {"user_answers": data.get("answers", {})})
    elif request.action == "approve":
        updates = {
            "plan_approved": True, 
            "plan_edits": data.get("edits", ""),
            "research_mode": data.get("mode", "deep")
        }
        # The user may edit the plan before approving; downstream agents read research_plan
        edited_plan = data.get("plan")
        if edited_plan is not None:
            if not isinstance(edited_plan, dict) or not isinstance(edited_plan.get("sections"), list) or not edited_plan["sections"]:
                raise HTTPException(status_code=400, detail="Edited plan must contain at least one section")
            updates["research_plan"] = edited_plan
        await graph.aupdate_state(config, updates)
    elif request.action == "continue":
        await graph.aupdate_state(config, {})
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    async def mark_completed():
        supabase = get_supabase_client()
        await asyncio.to_thread(supabase.table("sessions").update({"status": "completed"}).eq("thread_id", request.thread_id).execute)

    return EventSourceResponse(stream_graph(graph, None, config, request.thread_id, on_complete=mark_completed), ping=20)

@router.get("/{thread_id}")
async def get_research_session(thread_id: str, req: Request, user=Depends(get_current_user)):
    """Saved state of a research session, so the dashboard can reopen it from history."""
    await verify_session(thread_id, user.id)
    snapshot = await req.app.state.graph.aget_state({"configurable": {"thread_id": thread_id}})
    values = snapshot.values or {}
    return {
        "thread_id": thread_id,
        "next": list(snapshot.next),
        "state": {k: values[k] for k in SESSION_FIELDS if k in values},
    }
