import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

import graph.brainstorm
from api.routers import brainstorm
from graph.brainstorm import build_brainstorm_graph
from utils.auth import get_current_user

@pytest.fixture
def chat(monkeypatch):
    seen = {"llm_inputs": [], "inserts": []}

    async def fake_llm(messages, agent_name=None, temperature=0.2):
        seen["llm_inputs"].append(messages)
        return AIMessage(content=f"reply {len(seen['llm_inputs'])}")

    class FakeTable:
        def insert(self, row):
            seen["inserts"].append(row)
            return self
        def execute(self):
            return None

    async def owns_session(thread_id, user_id):
        return None

    monkeypatch.setattr(graph.brainstorm, "ainvoke_llm", fake_llm)
    monkeypatch.setattr(brainstorm, "get_supabase_client", lambda: type("SB", (), {"table": lambda self, n: FakeTable()})())
    monkeypatch.setattr(brainstorm, "verify_session", owns_session)

    async def record_profile(user):
        seen.setdefault("profiles", []).append(user.id)
    monkeypatch.setattr(brainstorm, "ensure_profile", record_profile)

    app = FastAPI()
    app.include_router(brainstorm.router)
    app.state.brainstorm_graph = build_brainstorm_graph(MemorySaver())
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()
    return TestClient(app), seen

def send(http, message, chat_id=None):
    """POST a message; return (streamed reply text, chat_id from the done event)."""
    body = {"message": message, **({"chat_id": chat_id} if chat_id else {})}
    with http.stream("POST", "/api/research/brainstorm", json=body) as res:
        assert res.status_code == 200
        text = "".join(res.iter_text())
    events = [json.loads(line[5:]) for line in text.splitlines() if line.startswith("data:")]
    reply = "".join(e.get("token", "") for e in events)
    done = [e for e in events if e.get("status") == "completed"]
    assert done, text
    return reply, done[0]["thread_id"]

def test_new_chat_is_saved_to_history(chat):
    http, seen = chat
    reply, chat_id = send(http, "Can small models verify big ones?")

    assert reply == "reply 1"  # non-streaming reply still reaches the client
    assert seen["profiles"] == ["u"]  # profile guaranteed before the sessions insert
    assert seen["inserts"] == [{
        "thread_id": chat_id, "user_id": "u", "topic": "Can small models verify big ones?",
        "research_mode": "brainstorm", "status": "active",
    }]

def test_follow_up_keeps_history_and_can_be_reloaded(chat):
    http, seen = chat
    _, chat_id = send(http, "First idea")
    reply, same_id = send(http, "Follow-up", chat_id=chat_id)

    assert same_id == chat_id and reply == "reply 2"
    assert len(seen["inserts"]) == 1  # no duplicate history entry
    # system + user + assistant + user
    assert [m.type for m in seen["llm_inputs"][1]] == ["system", "human", "ai", "human"]

    res = http.get(f"/api/research/brainstorm/{chat_id}")
    assert res.json()["messages"] == [
        {"role": "user", "content": "First idea"},
        {"role": "assistant", "content": "reply 1"},
        {"role": "user", "content": "Follow-up"},
        {"role": "assistant", "content": "reply 2"},
    ]

def test_empty_message_is_rejected(chat):
    http, _ = chat
    assert http.post("/api/research/brainstorm", json={"message": "   "}).status_code == 400
