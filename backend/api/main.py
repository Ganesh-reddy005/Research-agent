import json
import uuid
import os
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import shutil
from contextlib import asynccontextmanager

from graph.workflow import build_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver

from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from utils.llm import OpenRouterEmbeddings, ainvoke_llm
from utils.auth import get_current_user, get_supabase_client
from utils.ingestion import process_pdf_ingestion
from agents.brainstorm import brainstorm_chat
from langchain_core.messages import SystemMessage, HumanMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
            await checkpointer.setup()
            app.state.graph = build_graph(checkpointer=checkpointer)
            yield
    else:
        print("WARNING: DATABASE_URL not found, falling back to MemorySaver")
        app.state.graph = build_graph(checkpointer=MemorySaver())
        yield

app = FastAPI(title="AI Research Production System API", lifespan=lifespan)

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

class BrainstormRequest(BaseModel):
    messages: List[Dict[str, str]]

async def verify_session(thread_id: str, user_id: str):
    supabase = get_supabase_client()
    try:
        res = supabase.table("sessions").select("user_id").eq("thread_id", thread_id).execute()
        if not res.data or res.data[0]["user_id"] != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/")
def home():
    return {"message": "AI Research Production System"}

@app.post("/api/research/start")
async def start_research(request: ResearchStartRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.graph
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Record session in Supabase
    supabase = get_supabase_client()
    try:
        supabase.table("sessions").insert({
            "thread_id": thread_id,
            "user_id": user.id,
            "topic": request.topic,
            "research_mode": request.mode or "deep",
            "status": "active"
        }).execute()
    except Exception as e:
        # If DB fails, we still might want to proceed or fail early
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
async def resume_research(request: ResearchResumeRequest, req: Request, user=Depends(get_current_user)):
    graph = req.app.state.graph
    # Verify ownership
    await verify_session(request.thread_id, user.id)
    
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
                # Update status in Supabase when done
                supabase = get_supabase_client()
                supabase.table("sessions").update({"status": "completed"}).eq("thread_id", request.thread_id).execute()
                
                yield {"event": "done", "data": json.dumps({"thread_id": request.thread_id, "status": "completed"})}
        except Exception as e:
            print(f"SSE Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            
    return EventSourceResponse(event_generator(), ping=20)

@app.post("/api/library/upload")
async def upload_document(file: UploadFile = File(...), user=Depends(get_current_user)):
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        collection_name = await process_pdf_ingestion(temp_path, user.id, file.filename)
        
        supabase = get_supabase_client()
        supabase.table("library").insert({
            "user_id": user.id,
            "filename": file.filename,
            "storage_path": f"library/{user.id}/{file.filename}", 
            "parsing_status": "completed",
            "qdrant_collection_name": collection_name
        }).execute()
        
        return {"status": "success", "filename": file.filename, "collection": collection_name}
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/library")
async def list_library(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    res = supabase.table("library").select("*").eq("user_id", user.id).execute()
    return res.data

@app.get("/api/sessions")
async def list_sessions(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    res = supabase.table("sessions").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    return res.data

@app.post("/api/research/brainstorm")
async def brainstorm_research(request: BrainstormRequest, user=Depends(get_current_user)):
    async def event_generator():
        try:
            async for chunk in brainstorm_chat(request.messages):
                yield {"event": "thought", "data": json.dumps({"agent": "brainstorm", "token": chunk})}
            yield {"event": "done", "data": json.dumps({"status": "completed"})}
        except Exception as e:
            print(f"Brainstorm Error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator(), ping=20)

@app.post("/api/research/chat")
async def chat_with_data(request: ChatRequest, user=Depends(get_current_user)):
    # Verify ownership
    await verify_session(request.thread_id, user.id)
    
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
