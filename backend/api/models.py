from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class ResearchStartRequest(BaseModel):
    topic: str
    mode: Optional[str] = "deep"

class ResearchResumeRequest(BaseModel):
    thread_id: str
    action: str # "answer", "approve", or "continue"
    data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    thread_id: str
    query: str
    history: List[Dict[str, str]] = []  # earlier turns of the source chat, oldest first

class BrainstormRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None  # omit to start a new conversation
