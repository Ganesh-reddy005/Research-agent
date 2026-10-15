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

    async def event_generator():
        state = {
            "topic": request.topic, 
            "research_mode": request.mode or "deep", 
            "thread_id": thread_id,
            "user_id": str(user.id)
        }
        try:
            async for event in graph.astream_events(state, config=config, version="v2"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {
                            "event": "thought",
                            "data": json.dumps({
                                "thread_id": thread_id, 
                                "agent": event["metadata"].get("langgraph_node", "agent"), 
                                "token": content
                            })
                        }
                
                elif kind == "on_chain_end":
                    if "langgraph_node" in event["metadata"]:
                        output = event["data"].get("output")
                        if output and isinstance(output, dict):
                            yield {
                                "event": "step",
                                "data": json.dumps({
                                    "thread_id": thread_id, 
                                    "step": event["metadata"]["langgraph_node"], 
                                    "state": output
                                })
                            }
            
            snapshot = await graph.aget_state(config)
            if snapshot.next:
                yield {
                    "event": "interrupt",
                    "data": json.dumps({"thread_id": thread_id, "next": snapshot.next})
                }
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)

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

    async def event_generator():
        try:
            async for event in graph.astream_events(None, config=config, version="v2"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {
                            "event": "thought",
                            "data": json.dumps({
                                "thread_id": request.thread_id, 
                                "agent": event["metadata"].get("langgraph_node", "agent"), 
                                "token": content
                            })
                        }
                
                elif kind == "on_chain_end":
                    if "langgraph_node" in event["metadata"]:
                        output = event["data"].get("output")
                        if output and isinstance(output, dict):
                            yield {
                                "event": "step",
                                "data": json.dumps({
                                    "thread_id": request.thread_id, 
                                    "step": event["metadata"]["langgraph_node"], 
                                    "state": output
                                })
                            }
                    
            snapshot = await graph.aget_state(config)
            if snapshot.next:
                yield {
                    "event": "interrupt",
                    "data": json.dumps({"thread_id": request.thread_id, "next": snapshot.next})
                }
            else:
                supabase = get_supabase_client()
                await asyncio.to_thread(supabase.table("sessions").update({"status": "completed"}).eq("thread_id", request.thread_id).execute)
                
                yield {"event": "done", "data": json.dumps({"thread_id": request.thread_id, "status": "completed"})}
        except Exception as e:
            print(f"SSE Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)

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
