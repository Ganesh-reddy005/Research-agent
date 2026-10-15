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
