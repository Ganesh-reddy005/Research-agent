import json
import uuid
import asyncio
from fastapi import APIRouter, Request, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from api.models import ResearchStartRequest, ResearchResumeRequest, ExperimentBriefRequest
from experiments.brief import normalise_brief, missing_fields
from api.experiment_actions import ACTIONS as EXPERIMENT_ACTIONS, experiment_update
from utils.auth import get_current_user, get_supabase_client, verify_session, ensure_profile
from repo.github import parse_github_url, RepoError

router = APIRouter(prefix="/api/research", tags=["research"])

# State fields the dashboard needs to restore a session
SESSION_FIELDS = [
    "topic", "research_mode", "clarification_questions", "user_answers", "research_brief",
    "research_plan", "raw_sources", "assistance_summary", "draft_report", "final_report",
    "citation_audit_log", "current_step", "repo_url", "project_profile", "target_pages", "search_plan", "experiment_brief", "lab", "notebook", "last_attempt",
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
            # The step that paused tells apart two pauses before the same node (review vs. brief)
            yield event("interrupt", next=snapshot.next, step=snapshot.values.get("current_step"))
        else:
            if on_complete:
                await on_complete()
            yield event("done", status="completed")
    except Exception as e:
        print(f"SSE Error: {e}")
        yield {"event": "error", "data": json.dumps({"error": str(e)})}

def initial_state(request: ResearchStartRequest) -> tuple[dict, str]:
    """Graph input for a new session and its title in History: a topic, or a repository
    (whose analysed project becomes the topic)."""
    state = {"research_mode": request.mode or "deep"}
    if request.pages:
        state["target_pages"] = request.pages
    if not request.repo_url:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Enter a research topic or a GitHub repository link")
        return {**state, "topic": request.topic}, request.topic
    try:
        repo = parse_github_url(request.repo_url)
    except RepoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # repo_ingest sets the topic from the project; History names the session after the repository
    project = {"topic": "", "repo_url": request.repo_url.strip(), "project_notes": request.topic.strip()}
    return {**state, **project}, repo.full_name

@router.post("/start")
async def start_research(request: ResearchStartRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.graph
    state, session_title = initial_state(request)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Record session in Supabase
    supabase = get_supabase_client()
    try:
        await ensure_profile(user)
        await asyncio.to_thread(supabase.table("sessions").insert({
            "thread_id": thread_id,
            "user_id": user.id,
            "topic": session_title,
            "research_mode": state["research_mode"],
            "status": "active"
        }).execute)
    except Exception as e:
        print(f"Failed to record session: {e}")
        raise HTTPException(status_code=500, detail="Could not initialize research session in database")

    state.update(thread_id=thread_id, user_id=str(user.id))
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
    elif request.action in EXPERIMENT_ACTIONS:
        values = (await graph.aget_state(config)).values or {}
        await graph.aupdate_state(config, experiment_update(request.action, values, data))
    elif request.action == "plan_experiments":
        await graph.aupdate_state(config, {"wants_experiments": True})
    elif request.action == "continue":
        await graph.aupdate_state(config, {})
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    async def mark_completed():
        supabase = get_supabase_client()
        await asyncio.to_thread(supabase.table("sessions").update({"status": "completed"}).eq("thread_id", request.thread_id).execute)

    return EventSourceResponse(stream_graph(graph, None, config, request.thread_id, on_complete=mark_completed), ping=20)

@router.put("/{thread_id}/brief")
async def save_experiment_brief(thread_id: str, request: ExperimentBriefRequest, req: Request, user=Depends(get_current_user)):
    """Save the user's edits to the experiment brief while the session is paused on it."""
    await verify_session(thread_id, user.id)
    graph, config = req.app.state.graph, {"configurable": {"thread_id": thread_id}}
    snapshot = await graph.aget_state(config)
    if (snapshot.values or {}).get("current_step") != "experiment_brief" or not snapshot.next:
        raise HTTPException(status_code=409, detail="This session isn't waiting on an experiment brief")
    brief = normalise_brief(request.brief, default_target=snapshot.values.get("repo_url", ""))
    await graph.aupdate_state(config, {"experiment_brief": brief})
    return {"brief": brief, "missing": missing_fields(brief)}

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
