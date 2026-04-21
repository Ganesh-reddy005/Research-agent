import json
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from graph.workflow import build_graph

load_dotenv()

app = FastAPI(title="AI Research Production System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchStartRequest(BaseModel):
    topic: str
    mode: Optional[str] = "deep"

class ResearchResumeRequest(BaseModel):
    thread_id: str
    action: str # "answer" or "approve"
    data: Optional[Dict[str, Any]] = None

graph = build_graph()

@app.post("/api/research/start")
async def start_research(request: ResearchStartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    async def event_generator():
        state = {"topic": request.topic, "research_mode": "deep"} # Default to deep 
        try:
            async for event in graph.astream_events(state, config=config, version="v2"):
                kind = event["event"]
                
                # Token Streaming (Thinking)
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
                
                # State Updates (Step completion)
                elif kind == "on_chain_end":
                    # We only care about node completions
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
            
            # Check for interrupts
            snapshot = await graph.aget_state(config)
            if snapshot.next:
                yield {
                    "event": "interrupt",
                    "data": json.dumps({"thread_id": thread_id, "next": snapshot.next})
                }
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)

@app.post("/api/research/resume")
async def resume_research(request: ResearchResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    if request.action == "answer":
        await graph.aupdate_state(config, {"user_answers": request.data.get("answers", {})})
    elif request.action == "approve":
        # Pass the research_mode if provided during approval/start
        await graph.aupdate_state(config, {
            "plan_approved": True, 
            "plan_edits": request.data.get("edits", ""),
            "research_mode": request.data.get("mode", "deep")
        })
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
                yield {"event": "done", "data": json.dumps({"thread_id": request.thread_id, "status": "completed"})}
        except Exception as e:
            print(f"SSE Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)
