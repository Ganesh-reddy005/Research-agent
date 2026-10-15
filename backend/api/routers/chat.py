import asyncio
from fastapi import APIRouter, Depends, HTTPException
from api.models import ChatRequest
from utils.auth import get_current_user, verify_session
from utils.llm import ainvoke_llm
from utils.vectorstore import qdrant_configured, research_collection, collection_exists, get_vector_store
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter(prefix="/api/research/chat", tags=["research"])

@router.post("")
async def chat_with_data(request: ChatRequest, user=Depends(get_current_user)):
    await verify_session(request.thread_id, user.id)
    
    if not qdrant_configured():
        raise HTTPException(status_code=500, detail="Qdrant not configured")
        
    collection_name = research_collection(request.thread_id)
    
    docs = []
    if await asyncio.to_thread(collection_exists, collection_name):
        docs = await get_vector_store(collection_name).asimilarity_search(request.query, k=5)
    
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
    
    source_titles = list(set([d.metadata.get("title") for d in docs if d.metadata.get("title")]))
    
    return {"answer": response.content.strip(), "sources": source_titles}
