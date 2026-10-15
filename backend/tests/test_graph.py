import asyncio
import time
import pytest

import agents.retriever
from conftest import PLAN

async def run_to_end(graph, state, config):
    await graph.ainvoke(state, config)        # -> pauses after clarification
    await graph.ainvoke(None, config)         # -> pauses after planning
    await graph.ainvoke(None, config)         # -> pauses after assistance
    return await graph.ainvoke(None, config)  # -> runs to END

def test_full_pipeline_runs_and_user_id_reaches_private_library(offline_graph):
    graph, calls = offline_graph
    config = {"configurable": {"thread_id": "t-1"}}
    state = {"topic": "x", "research_mode": "light", "thread_id": "t-1", "user_id": "user-123"}

    final = asyncio.run(run_to_end(graph, state, config))

    # Regression: user_id was not declared in AgentState, so LangGraph dropped it
    # and the private library was never searched.
    assert calls["private"] and set(calls["private"]) == {"user-123"}
    assert final["final_report"] == "Final paper citing [1]."
    assert final["citation_audit_log"]["unique_sources_cited"] == 1
    assert any(s["source"] == "Private Library" for s in final["raw_sources"])

def test_retriever_source_order_is_deterministic(offline_graph):
    graph, _ = offline_graph
    state = {"topic": "x", "research_mode": "light", "research_plan": PLAN["research_plan"], "user_id": "u"}
    first = asyncio.run(agents.retriever.retriever_node(state))["raw_sources"]
    second = asyncio.run(agents.retriever.retriever_node(state))["raw_sources"]
    # Citations [n] map to raw_sources[n-1], so the order must not depend on API latency.
    assert [s["url"] for s in first] == [s["url"] for s in second]

def test_retriever_does_not_block_event_loop(offline_graph, monkeypatch):
    def slow_search(query, max_results=3):
        time.sleep(0.4)  # a slow, synchronous HTTP call
        return []
    for name in ["search_openalex", "search_arxiv", "search_core", "search_private_library"]:
        monkeypatch.setattr(agents.retriever, name, lambda *a, **k: slow_search(a[0]))

    async def scenario():
        ticks = 0
        async def heartbeat():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.02)
                ticks += 1
        hb = asyncio.create_task(heartbeat())
        state = {"topic": "x", "research_mode": "light", "research_plan": PLAN["research_plan"], "user_id": "u"}
        await agents.retriever.retriever_node(state)
        hb.cancel()
        return ticks

    # Other requests (heartbeat) must keep running while searches are in flight.
    assert asyncio.run(scenario()) >= 5

def test_writer_cites_with_reference_numbers(monkeypatch):
    from agents import writer
    from agents.writer import number_evidence
    sources = [{"url": "u1", "title": "Paper A"}, {"url": "u2", "title": "Paper B"}]
    # Passages are labelled by their position in raw_sources; unknown sources are dropped
    text = number_evidence([("b text", "u2", "Paper B"), ("? text", "elsewhere", "X"), ("a text", "u1", "Paper A")], sources)
    assert text == "[2] Paper B\nb text\n\n[1] Paper A\na text"

    prompts = []
    async def capture(messages, **kwargs):
        prompts.append(messages[0].content)
        from langchain_core.messages import AIMessage
        return AIMessage(content="Body [1].")
    monkeypatch.setattr(writer, "ainvoke_llm", capture)
    state = {"topic": "t", "research_plan": PLAN["research_plan"], "raw_sources": [
        {"url": "u1", "title": "Paper A", "summary": "about A"}]}
    out = asyncio.run(writer.writer_node(state))
    assert "[1] Paper A\nabout A" in prompts[0]  # evidence carries citation numbers
    assert out["draft_report"].strip() == "## Introduction\n\nBody [1]."

def test_sources_are_interleaved_across_queries(offline_graph):
    state = {"topic": "x", "research_mode": "light", "research_plan": PLAN["research_plan"], "user_id": "u"}
    sources = asyncio.run(agents.retriever.retriever_node(state))["raw_sources"]
    # The first few sources (the ones read in full) cover both queries, not just the first
    first = [s["title"] for s in sources[:6]]
    assert any("query one" in t for t in first) and any("query two" in t for t in first)

def test_llm_retries_transient_errors_only(monkeypatch):
    import httpx, openai
    from utils import llm as llm_mod
    real_sleep = asyncio.sleep
    async def no_wait(*_):
        await real_sleep(0)
    monkeypatch.setattr(llm_mod.asyncio, "sleep", no_wait)

    class Flaky:
        def __init__(self, errors): self.errors, self.calls = list(errors), 0
        async def ainvoke(self, messages):
            self.calls += 1
            if self.errors:
                raise self.errors.pop(0)
            return "ok"

    flaky = Flaky([RuntimeError("Stream ended before a terminal response event")])
    assert asyncio.run(llm_mod.ainvoke_with_retry(flaky, [])) == "ok" and flaky.calls == 2

    response = httpx.Response(400, request=httpx.Request("POST", "https://x"))
    bad = Flaky([openai.BadRequestError("bad", response=response, body=None)])
    with pytest.raises(openai.BadRequestError):
        asyncio.run(llm_mod.ainvoke_with_retry(bad, []))
    assert bad.calls == 1  # not retried
