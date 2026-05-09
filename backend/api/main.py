import json
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os

from graph.workflow import build_graph
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from utils.llm import OpenRouterEmbeddings, ainvoke_llm
from langchain_core.messages import SystemMessage, HumanMessage

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
    action: str # "answer", "approve", or "continue"
    data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    thread_id: str
    query: str

graph = build_graph()

@app.get("/")
def home():
    return {"message": "AI Research Production System"}

@app.post("/api/research/start")
async def start_research(request: ResearchStartRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    async def event_generator():
        state = {"topic": request.topic, "research_mode": "deep", "thread_id": thread_id} # Default to deep 
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
    elif request.action == "continue":
        # Just resume workflow without explicit state updates
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
                yield {"event": "done", "data": json.dumps({"thread_id": request.thread_id, "status": "completed"})}
        except Exception as e:
            print(f"SSE Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)

@app.post("/api/research/chat")
async def chat_with_data(request: ChatRequest):
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        raise HTTPException(status_code=500, detail="Qdrant not configured")
        
    embeddings = OpenRouterEmbeddings()
    collection_name = f"research_{request.thread_id.replace('-', '_')}"
    
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url=qdrant_url,
        api_key=qdrant_api_key,
    )
    
    docs = vector_store.similarity_search(request.query, k=5)
    
    if not docs:
        return {"answer": "I couldn't find any information relevant to this in the documents.", "sources": []}
    
    context = "\n\n".join([f"Source: {d.metadata.get('title')}\n{d.page_content}" for d in docs])
    
    system_prompt = "You are a research assistant helping to answer questions using strictly the provided context. " \
                    "Answer concisely. If you don't know the answer based on the context, say so."
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {request.query}")
    ]
    
    response = await ainvoke_llm(messages, agent_name="chat")
    
    # Return unique sources
    source_titles = list(set([d.metadata.get("title") for d in docs if d.metadata.get("title")]))
    
    return {"answer": response.content.strip(), "sources": source_titles}
