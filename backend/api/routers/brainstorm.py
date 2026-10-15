import json
import uuid
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from api.models import BrainstormRequest
from utils.auth import get_current_user
from agents.brainstorm import brainstorm_chat

router = APIRouter(prefix="/api/research/brainstorm", tags=["research"])

@router.post("")
async def brainstorm_research(request: BrainstormRequest, user=Depends(get_current_user)):
    # Create a unique thread_id for this brainstorm turn if needed
    # though it's transient, the frontend expects a thread_id in data
    tid = f"brainstorm_{uuid.uuid4().hex[:8]}"
    
    async def event_generator():
        try:
            async for chunk in brainstorm_chat(request.messages):
                yield {
                    "event": "thought", 
                    "data": json.dumps({
                        "agent": "brainstorm", 
                        "token": chunk,
                        "thread_id": tid
                    })
                }
            yield {
                "event": "done", 
                "data": json.dumps({
                    "status": "completed",
                    "thread_id": tid
                })
            }
        except Exception as e:
            print(f"Brainstorm Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator(), ping=20)
