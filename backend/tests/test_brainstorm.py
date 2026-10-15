import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

import graph.brainstorm
from api.routers import brainstorm
from graph.brainstorm import build_brainstorm_graph, MAX_SEARCH_ROUNDS
from utils.auth import get_current_user

def search_call(i, tool="search_arxiv", query="sparse attention"):
    return AIMessage(content="", tool_calls=[{"name": tool, "args": {"query": query}, "id": f"call-{i}"}])

@pytest.fixture
def chat(monkeypatch):
    """Brainstorm API with a scripted model and fake search results. Set seen["script"] per test."""
    seen = {"llm_inputs": [], "allow_tools": [], "inserts": [], "searches": [], "script": []}

    class ScriptedLLM:
        def __init__(self, allow_tools):
            seen["allow_tools"].append(allow_tools)
            self.allow_tools = allow_tools

        async def ainvoke(self, messages):
            seen["llm_inputs"].append(messages)
            reply = seen["script"].pop(0) if seen["script"] else AIMessage(content=f"reply {len(seen['llm_inputs'])}")
            # A model with tool_choice="none" cannot call tools
            return reply if self.allow_tools or not reply.tool_calls else AIMessage(content="forced answer")

    async def fake_search(tool_name, args):
        query = args["query"]
        seen["searches"].append((tool_name, query))
        # Results are keyed by query, so the same query returns the same papers
        return [{"title": f"{tool_name} paper {i}", "url": f"https://example.org/{query}/{i}", "summary": "abstract",
                 "source": "arXiv", "year": 2026} for i in range(2)]

    class FakeTable:
        def insert(self, row):
            seen["inserts"].append(row)
            return self
        def execute(self):
            return None

    async def owns_session(thread_id, user_id):
        return None

    async def record_profile(user):
        seen.setdefault("profiles", []).append(user.id)

    monkeypatch.setattr(graph.brainstorm, "get_brainstorm_llm", ScriptedLLM)
    monkeypatch.setattr(graph.brainstorm, "run_search", fake_search)
    monkeypatch.setattr(brainstorm, "get_supabase_client", lambda: type("SB", (), {"table": lambda self, n: FakeTable()})())
    monkeypatch.setattr(brainstorm, "verify_session", owns_session)
    monkeypatch.setattr(brainstorm, "ensure_profile", record_profile)

    app = FastAPI()
    app.include_router(brainstorm.router)
    app.state.brainstorm_graph = build_brainstorm_graph(MemorySaver())
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()
    return TestClient(app), seen

def send(http, message, chat_id=None):
    """POST a message; return (reply text, chat_id, list of (event, data))."""
    body = {"message": message, **({"chat_id": chat_id} if chat_id else {})}
    with http.stream("POST", "/api/research/brainstorm", json=body) as res:
        assert res.status_code == 200
        raw = "".join(res.iter_text())
    events, current = [], None
    for line in raw.splitlines():
        if line.startswith("event:"):
            current = line[6:].strip()
        elif line.startswith("data:"):
            events.append((current, json.loads(line[5:])))
    reply = "".join(d.get("token", "") for e, d in events if e == "thought")
    done = [d for e, d in events if e == "done"]
    assert done, raw
    return reply, done[0]["thread_id"], events

def test_new_chat_is_saved_to_history(chat):
    http, seen = chat
    reply, chat_id, events = send(http, "Can small models verify big ones?")

    assert reply == "reply 1"  # answered without searching
    assert not [e for e, _ in events if e and e.startswith("search")]
    assert seen["profiles"] == ["u"]  # profile guaranteed before the sessions insert
    assert seen["inserts"] == [{
        "thread_id": chat_id, "user_id": "u", "topic": "Can small models verify big ones?",
        "research_mode": "brainstorm", "status": "active",
    }]

def test_search_streams_progress_and_cited_answer(chat):
    http, seen = chat
    seen["script"] = [search_call(1), AIMessage(content="Gated sparse attention [1] helps [2].")]

    reply, chat_id, events = send(http, "What's new in sparse attention?")

    names = [e for e, _ in events]
    assert names.index("search_start") < names.index("search_end") < names.index("thought")
    start = dict(events)["search_start"]
    end = dict(events)["search_end"]
    assert start == {"id": "call-1", "tool": "search_arxiv", "query": "sparse attention"}
    assert [s["n"] for s in end["sources"]] == [1, 2]
    assert "summary" not in end["sources"][0]  # abstracts stay server-side
    assert reply == "Gated sparse attention [1] helps [2]."
    # The model read the numbered results before answering
    tool_msg = seen["llm_inputs"][1][-1]
    assert tool_msg.type == "tool" and "[1] search_arxiv paper 0 (arXiv, 2026)" in tool_msg.content

    # Reopening the chat brings back the searches with the answer
    saved = http.get(f"/api/research/brainstorm/{chat_id}").json()["messages"]
    assert saved[0] == {"role": "user", "content": "What's new in sparse attention?"}
    assert saved[1]["content"] == reply
    assert saved[1]["searches"][0]["query"] == "sparse attention"
    assert [s["n"] for s in saved[1]["searches"][0]["sources"]] == [1, 2]

def test_sources_are_numbered_across_searches_in_a_turn(chat):
    http, seen = chat
    seen["script"] = [search_call(1), search_call(2, tool="web_search", query="news"), AIMessage(content="done")]
    _, _, events = send(http, "Compare")
    ends = [d for e, d in events if e == "search_end"]
    assert [s["n"] for s in ends[0]["sources"]] == [1, 2]
    assert [s["n"] for s in ends[1]["sources"]] == [3, 4]

def test_search_rounds_are_capped(chat):
    http, seen = chat
    seen["script"] = [search_call(i) for i in range(10)]  # a model that never stops searching
    reply, _, _ = send(http, "Search forever")
    assert len(seen["searches"]) == MAX_SEARCH_ROUNDS
    assert seen["allow_tools"][-1] is False and reply == "forced answer"

def test_follow_up_keeps_history_and_numbering_restarts(chat):
    http, seen = chat
    seen["script"] = [search_call(1), AIMessage(content="first")]
    _, chat_id, _ = send(http, "First idea")
    seen["script"] = [search_call(2), AIMessage(content="second")]
    _, same_id, events = send(http, "Follow-up", chat_id=chat_id)

    assert same_id == chat_id and len(seen["inserts"]) == 1  # no duplicate history entry
    assert [s["n"] for s in dict(events)["search_end"]["sources"]] == [1, 2]  # per-turn numbering
    saved = http.get(f"/api/research/brainstorm/{chat_id}").json()["messages"]
    assert [m["role"] for m in saved] == ["user", "assistant", "user", "assistant"]
    assert [m["content"] for m in saved if m["role"] == "assistant"] == ["first", "second"]

def test_empty_message_is_rejected(chat):
    http, _ = chat
    assert http.post("/api/research/brainstorm", json={"message": "   "}).status_code == 400

def test_same_paper_from_two_searches_keeps_one_number(chat):
    http, seen = chat
    duplicate = AIMessage(content="", tool_calls=[
        {"name": "search_arxiv", "args": {"query": "q"}, "id": "a"},
        {"name": "search_openalex", "args": {"query": "q"}, "id": "b"},  # same URLs as "a"
    ])
    seen["script"] = [duplicate, search_call(2, query="other"), AIMessage(content="done")]
    _, _, events = send(http, "Dedupe")
    ends = [d for e, d in events if e == "search_end"]
    assert [s["n"] for s in ends[0]["sources"]] == [1, 2]
    assert [s["n"] for s in ends[1]["sources"]] == [1, 2]  # reused, not [3, 4]
    assert [s["n"] for s in ends[2]["sources"]] == [3, 4]

def test_newest_first_reaches_arxiv(monkeypatch):
    import asyncio
    import agents.search_tools as tools
    calls = []
    monkeypatch.setitem(tools._SEARCHERS, "search_arxiv", lambda q, **kw: calls.append((q, kw)) or [])
    asyncio.run(tools.run_search("search_arxiv", {"query": "sparse attention", "newest_first": True}))
    asyncio.run(tools.run_search("search_arxiv", {"query": "sparse attention"}))
    assert calls == [("sparse attention", {"max_results": 5, "newest_first": True}),
                     ("sparse attention", {"max_results": 5})]

def test_preamble_and_answer_are_separate_paragraphs():
    from langchain_core.messages import HumanMessage, ToolMessage
    from api.routers.brainstorm import to_chat_messages
    saved = to_chat_messages([
        HumanMessage(content="q"),
        AIMessage(content="Let me check.", tool_calls=[{"name": "web_search", "args": {"query": "x"}, "id": "c"}]),
        ToolMessage(content="...", tool_call_id="c", name="web_search", artifact={"tool": "web_search", "query": "x", "sources": []}),
        AIMessage(content="Answer [1]."),
    ])
    assert saved[1]["content"] == "Let me check.\n\nAnswer [1]."

def test_forced_answer_gets_results_as_text_not_tool_calls(chat):
    http, seen = chat
    seen["script"] = [search_call(i) for i in range(10)]
    send(http, "Search forever")
    final_input = seen["llm_inputs"][-1]
    assert not any(m.type == "tool" or getattr(m, "tool_calls", None) for m in final_input)
    assert "Search results gathered for this question" in final_input[-1].content
    assert "[1] search_arxiv paper 0" in final_input[-1].content

def test_earlier_turns_are_sent_without_their_search_results(chat):
    http, seen = chat
    seen["script"] = [search_call(1), AIMessage(content="first answer")]
    _, chat_id, _ = send(http, "First")
    send(http, "Second", chat_id=chat_id)
    second_turn_input = seen["llm_inputs"][-1]
    assert [m.type for m in second_turn_input] == ["system", "human", "ai", "human"]
    assert second_turn_input[2].content == "first answer"

def test_arxiv_newest_first_requires_every_topic_term():
    from agents.retriever import _arxiv_all_terms
    assert _arxiv_all_terms("latest sparse attention for long-context LLMs 2026") == \
        "all:sparse AND all:attention AND all:long AND all:context AND all:LLMs"
