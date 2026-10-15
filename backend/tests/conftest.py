import os
import sys

# Pin every external-service variable BEFORE any app module runs load_dotenv(),
# which never overrides variables that are already set. Tests must not touch
# real keys, Qdrant, Supabase or Postgres.
TEST_ENV = {
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "GROQ_API_KEY": "test-groq-key",
    "TAVILY_API_KEY": "",
    "CORE_API_KEY": "",
    "OPENALEX_API_KEY": "",
    "QDRANT_URL": "",
    "QDRANT_API_KEY": "",
    "SUPABASE_URL": "",
    "SUPABASE_SERVICE_ROLE_KEY": "",
    "DATABASE_URL": "",
}
os.environ.update(TEST_ENV)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---- Offline graph fixture (shared) --------------------------------------
import json
import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

import agents.clarification, agents.planning, agents.retriever, agents.assistance
import agents.synthesis, agents.writer, agents.critic, agents.refinement
from graph.workflow import build_graph

LLM_MODULES = [agents.clarification, agents.planning, agents.retriever, agents.assistance,
               agents.synthesis, agents.writer, agents.critic, agents.refinement]

PLAN = {
    "research_brief": "Brief.",
    "research_plan": {
        "objective": "Obj",
        "sections": [{"title": "Introduction", "description": "Intro", "questions": ["Q?"]}],
        "expected_outcome": "Out",
    },
}

async def fake_llm(messages, agent_name=None, temperature=0.2, **kwargs):
    canned = {
        "clarification": json.dumps([{"id": "1", "question": "Scope?"}]),
        "planning": json.dumps(PLAN),
        "retrieval": json.dumps(["query one", "query two"]),
        "refinement": "Final paper citing [1].",
    }
    return AIMessage(content=canned.get(agent_name, f"{agent_name} output"))

@pytest.fixture
def offline_graph(monkeypatch):
    """The real graph with every LLM and search API replaced by fakes."""
    for mod in LLM_MODULES:
        monkeypatch.setattr(mod, "ainvoke_llm", fake_llm)
    calls = {"private": []}

    def fake_private(query, user_id, max_results=5):
        calls["private"].append(user_id)
        return [{"title": "My PDF", "url": "local://my.pdf", "summary": "s", "source": "Private Library"}]

    def fake_public(name):
        return lambda query, max_results=3: [
            {"title": f"{name}:{query}", "url": f"https://{name}/{query}", "summary": "s", "source": name}]

    monkeypatch.setattr(agents.retriever, "search_private_library", fake_private)
    monkeypatch.setattr(agents.retriever, "search_openalex", fake_public("openalex"))
    monkeypatch.setattr(agents.retriever, "search_arxiv", fake_public("arxiv"))
    monkeypatch.setattr(agents.retriever, "search_core", lambda q, max_results=3: [])
    return build_graph(checkpointer=MemorySaver()), calls

