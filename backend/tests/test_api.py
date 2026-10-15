import asyncio
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers import research
from utils.auth import get_current_user
from conftest import PLAN

THREAD = "thread-api"
CONFIG = {"configurable": {"thread_id": THREAD}}

@pytest.fixture
def client(offline_graph, monkeypatch):
    graph, _ = offline_graph

    async def owns_session(thread_id, user_id):
        return None
    monkeypatch.setattr(research, "verify_session", owns_session)

    app = FastAPI()
    app.include_router(research.router)
    app.state.graph = graph
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()
    return TestClient(app), graph

def start(graph, pauses=1):
    async def run():
        await graph.ainvoke({"topic": "t", "research_mode": "light", "thread_id": THREAD, "user_id": "u"}, CONFIG)
        for _ in range(pauses - 1):
            await graph.ainvoke(None, CONFIG)
    asyncio.run(run())

def test_get_session_restores_state_and_next_step(client):
    http, graph = client
    start(graph)  # paused after clarification

    res = http.get(f"/api/research/{THREAD}")

    assert res.status_code == 200
    body = res.json()
    assert body["next"] == ["planning"]
    assert body["state"]["topic"] == "t"
    assert body["state"]["clarification_questions"][0]["question"] == "Scope?"
    assert "user_id" not in body["state"]  # internal fields are not exposed

def test_approve_with_edited_plan_replaces_research_plan(client):
    http, graph = client
    start(graph, pauses=2)  # paused after planning
    edited = {"objective": "Obj", "sections": [{"title": "Edited section", "description": "d", "questions": []}]}

    with http.stream("POST", "/api/research/resume",
                     json={"thread_id": THREAD, "action": "approve", "data": {"mode": "light", "plan": edited}}) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())

    assert "event: interrupt" in body  # ran retrieval and paused after assistance
    state = asyncio.run(graph.aget_state(CONFIG)).values
    assert state["research_plan"]["sections"][0]["title"] == "Edited section"

def test_approve_rejects_plan_without_sections(client):
    http, graph = client
    start(graph, pauses=2)
    res = http.post("/api/research/resume",
                    json={"thread_id": THREAD, "action": "approve", "data": {"plan": {"sections": []}}})
    assert res.status_code == 400

def test_resume_without_data_does_not_crash(client):
    http, graph = client
    start(graph)
    with http.stream("POST", "/api/research/resume", json={"thread_id": THREAD, "action": "answer"}) as res:
        assert res.status_code == 200

def test_stream_announces_agents_and_progress_without_json_tokens(client):
    http, graph = client
    start(graph, pauses=2)  # paused after planning
    with http.stream("POST", "/api/research/resume",
                     json={"thread_id": THREAD, "action": "approve", "data": {"mode": "light", "plan": PLAN["research_plan"]}}) as res:
        raw = "".join(res.iter_text())
    events = [(l[6:].strip(), json.loads(nxt[5:])) for l, nxt in zip(raw.splitlines(), raw.splitlines()[1:])
              if l.startswith("event:") and nxt.startswith("data:")]
    names = [e for e, _ in events]

    started = [d["agent"] for e, d in events if e == "agent_start"]
    assert started == ["retriever", "indexer", "assistance"]  # each announced as it begins
    progress = [d["message"] for e, d in events if e == "progress"]
    assert any(m.startswith("Searching 2 queries") for m in progress) and any(m.startswith("Found") for m in progress)
    assert names.index("agent_start") < names.index("progress") < names.index("step")
    # The retriever's LLM output is a JSON list of queries: never streamed to the UI
    assert not any(d.get("agent") == "retriever" for e, d in events if e == "thought")
