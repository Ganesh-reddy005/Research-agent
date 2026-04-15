import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from graph.workflow import build_graph

load_dotenv()

app = FastAPI(title="Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    query: str

app.graph = build_graph()

@app.post("/api/research")
async def research_endpoint(request: ResearchRequest):
    async def event_generator():
        query = request.query
        state = {"query": query}
        
        try:
            async for output in app.graph.astream(state, stream_mode="updates"):
                print(f"DEBUG BACKEND OUTPUT: {output}")
                for step_name, step_state in output.items():
                    yield {
                        "event": "step",
                        "data": json.dumps({"step": step_name, "state": step_state})
                    }
                    
            yield {
                "event": "done",
                "data": json.dumps({"status": "completed"})
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
            
    return EventSourceResponse(event_generator())
