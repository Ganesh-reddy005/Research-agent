from pydantic import BaseModel, Field
from agents.paper_length import MAX_PAGES
from typing import Dict, Any, Optional, List

class ResearchStartRequest(BaseModel):
    topic: str = ""  # the research question; for a repository, optional notes about the project
    mode: Optional[str] = "deep"
    repo_url: Optional[str] = None  # write up this repository's project instead of a topic
    pages: Optional[int] = Field(default=None, ge=1, le=MAX_PAGES)  # paper length in IEEE pages

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
