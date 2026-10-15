import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import utils.rag as rag
from api.routers import chat
from utils.auth import get_current_user

def P(title, text, url=None):
    return {"title": title, "text": text, "url": url or f"https://x/{title}", "source": "arXiv", "year": 2025}

CORPUS = [
    P("Benchmarks", "Syntax correctness of generated code is above 95% while security pass rates are lower."),
    P("Case study", "After instruction fine-tuning the specialized SLM achieved approximately 99% accuracy and 99.04% F1."),
    P("Survey", "Large models dominate code repair benchmarks; small models lag behind."),
]

def test_bm25_finds_exact_numbers_that_embeddings_miss():
    top = rag.bm25_rank("fine-tuned model 99% accuracy", CORPUS, k=2)
    assert top[0]["title"] == "Case study"
    assert rag.tokenize("approximately 99% accuracy, 99.04% F1") == ["approximately", "99", "accuracy", "99.04", "f1"]

def test_rank_fusion_rewards_agreement():
    a, b, c = CORPUS
    fused = rag.reciprocal_rank_fusion([a, b, c], [b, c])
    assert fused[0] is b  # ranked by both lists

def test_rerank_orders_by_score_caps_per_source_and_drops_irrelevant(monkeypatch):
    same = "https://x/paper"
    candidates = [P("p0", "t0", same), P("p1", "t1", same), P("p2", "t2", same), P("p3", "t3"), P("p4", "t4")]
    async def fake_llm(messages, **kw):
        return AIMessage(content='{"scores": [[0, 9], [1, 8], [2, 7], [3, 1], [4, 6]]}')
    monkeypatch.setattr(rag, "ainvoke_llm", fake_llm)
    picked = asyncio.run(rag.rerank("q", candidates, top_n=6, per_source=2))
    assert [p["title"] for p in picked] == ["p0", "p1", "p4"]  # p2: 3rd from same paper; p3: score 1

def test_rerank_falls_back_to_fused_order_on_bad_output(monkeypatch):
    async def broken(messages, **kw):
        return AIMessage(content="sorry, I can't")
    monkeypatch.setattr(rag, "ainvoke_llm", broken)
    picked = asyncio.run(rag.rerank("q", CORPUS, top_n=2))
    assert [p["title"] for p in picked] == ["Benchmarks", "Case study"]

def test_retrieve_uses_rewritten_query_and_searches_abstracts(monkeypatch):
    seen = {}
    async def fake_llm(messages, **kw):
        if "Rewrite" in messages[0].content:
            seen["rewrite_input"] = messages[1].content
            return AIMessage(content="How did the fine-tuned SLM achieve 99% accuracy?")
        return AIMessage(content='{"scores": []}')
    async def no_dense(collection, query, k=20):
        seen["dense_query"] = query
        return []
    monkeypatch.setattr(rag, "ainvoke_llm", fake_llm)
    monkeypatch.setattr(rag, "dense_search", no_dense)
    monkeypatch.setattr(rag, "collection_exists", lambda name: True)
    monkeypatch.setattr(rag, "load_chunks", lambda name: [])
    sources = [{"title": c["title"], "summary": c["text"], "url": c["url"], "source": "arXiv"} for c in CORPUS]

    query, passages = asyncio.run(rag.retrieve("col", "how did they achive 99%", [], "SLMs for code", "summary text", sources))

    assert query == seen["dense_query"] == "How did the fine-tuned SLM achieve 99% accuracy?"
    assert "summary text" in seen["rewrite_input"]  # pronouns resolved with the research summary
    assert passages[0]["title"] == "Case study"  # found via abstracts even with no indexed chunks

def test_chat_endpoint_numbers_sources_and_uses_history(monkeypatch):
    seen = {}
    async def fake_retrieve(collection, question, history, topic, summary, sources):
        seen["history"] = history
        chunk_without_year = {**P("Other", "x", "u2"), "year": None}  # indexed chunks carry no year
        return "rewritten", [P("Case study", "99% text", "u1"), P("Case study", "more", "u1"), chunk_without_year]
    async def fake_llm(messages, **kw):
        seen["messages"] = messages
        return AIMessage(content="They fine-tuned it [1].")
    async def ok(*a, **k):
        return None
    class Snapshot:
        values = {"topic": "t", "assistance_summary": "s", "raw_sources": [{"url": "u2", "year": 2024}]}
    class Graph:
        async def aget_state(self, config):
            return Snapshot()

    monkeypatch.setattr(chat, "retrieve", fake_retrieve)
    monkeypatch.setattr(chat, "ainvoke_llm", fake_llm)
    monkeypatch.setattr(chat, "verify_session", ok)
    monkeypatch.setattr(chat, "qdrant_configured", lambda: True)
    app = FastAPI()
    app.include_router(chat.router)
    app.state.graph = Graph()
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()

    history = [{"role": "user", "content": "earlier q"}, {"role": "assistant", "content": "earlier a"}]
    res = TestClient(app).post("/api/research/chat", json={"thread_id": "t", "query": "how?", "history": history}).json()

    assert res["search_query"] == "rewritten"
    assert [(s["n"], s["title"]) for s in res["sources"]] == [(1, "Case study"), (2, "Other")]  # one number per source
    assert res["sources"][1]["year"] == 2024
    assert seen["history"] == history
    assert [m.type for m in seen["messages"]] == ["system", "human", "ai", "human"]
    assert "[1] Case study\n99% text" in seen["messages"][-1].content
