from fastapi import APIRouter, Depends, HTTPException, Request
from api.models import ChatRequest
from utils.auth import get_current_user, verify_session
from utils.llm import ainvoke_llm
from utils.rag import retrieve
from utils.vectorstore import qdrant_configured, research_collection
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

router = APIRouter(prefix="/api/research/chat", tags=["research"])

SYSTEM_PROMPT = """You are a research assistant answering questions about the sources collected for a research project.
- Answer from the numbered passages. Cite them inline as [n] right after the claims they support.
- Be specific: include the methods, numbers and conditions the passages give.
- If the passages don't contain the answer, say what they do cover and what is missing. Never invent facts.
- Keep answers concise and conversational."""

@router.post("")
async def chat_with_data(request: ChatRequest, req: Request, user=Depends(get_current_user)):
    await verify_session(request.thread_id, user.id)
    if not qdrant_configured():
        raise HTTPException(status_code=500, detail="Qdrant not configured")

    snapshot = await req.app.state.graph.aget_state({"configurable": {"thread_id": request.thread_id}})
    state = snapshot.values or {}
    sources = state.get("raw_sources", [])
    history = [m for m in request.history if m.get("role") in ("user", "assistant") and m.get("content")]

    search_query, passages = await retrieve(
        research_collection(request.thread_id), request.query, history,
        state.get("topic", ""), state.get("assistance_summary", ""), sources,
    )
    if not passages:
        return {"answer": "I couldn't find anything about this in the collected sources.", "sources": [], "search_query": search_query}

    # Number passages by source (two passages from one paper share a number)
    year_by_url = {s.get("url"): s.get("year") for s in sources}
    numbered, cited = {}, []
    for p in passages:
        if p["url"] not in numbered:
            numbered[p["url"]] = len(cited) + 1
            cited.append({"n": numbered[p["url"]], "title": p["title"], "url": p["url"], "source": p["source"],
                          "year": p.get("year") or year_by_url.get(p["url"])})
    context = "\n\n".join(f"[{numbered[p['url']]}] {p['title']}\n{p['text']}" for p in passages)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in history[-6:]:
        messages.append(HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=f"Passages:\n{context}\n\nQuestion: {request.query}"))

    response = await ainvoke_llm(messages, agent_name="chat")
    return {"answer": response.content.strip(), "sources": cited, "search_query": search_query}
