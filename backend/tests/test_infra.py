import os
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

import utils.vectorstore as vs
from utils.llm import get_llm

@pytest.fixture
def memory_qdrant(monkeypatch):
    client = QdrantClient(location=":memory:")
    monkeypatch.setattr(vs, "get_qdrant_client", lambda: client)
    return client

def test_ensure_collection_uses_embedding_dim(memory_qdrant, monkeypatch):
    monkeypatch.setattr(vs, "embedding_dim", lambda: 2048)
    vs.ensure_collection("c1")
    assert memory_qdrant.get_collection("c1").config.params.vectors.size == 2048
    vs.ensure_collection("c1")  # idempotent

def test_ensure_collection_rejects_dim_mismatch(memory_qdrant, monkeypatch):
    monkeypatch.setattr(vs, "embedding_dim", lambda: 1024)
    vs.ensure_collection("c2")
    monkeypatch.setattr(vs, "embedding_dim", lambda: 2048)
    with pytest.raises(ValueError, match="vector size 1024"):
        vs.ensure_collection("c2")

def test_groq_prefix_routes_to_groq(monkeypatch):
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI
    monkeypatch.setenv("DEFAULT_MODEL", "groq:openai/gpt-oss-120b")
    llm = get_llm()
    assert isinstance(llm, ChatGroq) and llm.model_name == "openai/gpt-oss-120b"
    monkeypatch.setenv("DEFAULT_MODEL", "openai/gpt-5.4-mini")
    assert isinstance(get_llm(), ChatOpenAI)

def test_model_fallback_chain(monkeypatch):
    monkeypatch.setenv("ASSISTANCE_MODEL", "openai/gpt-5.4-mini")
    monkeypatch.setenv("DEFAULT_MODEL", "qwen/qwen3.8-27b")
    monkeypatch.delenv("CRITIC_MODEL", raising=False)
    assert get_llm("assistance").model_name == "openai/gpt-5.4-mini"  # per-agent var is honoured
    assert get_llm("critic").model_name == "qwen/qwen3.8-27b"         # unset -> DEFAULT_MODEL
    monkeypatch.delenv("DEFAULT_MODEL")
    assert get_llm("critic").model_name == "openai/gpt-5.4-mini"      # never a retired Groq model

def test_upload_filename_cannot_escape_temp_dir(monkeypatch):
    from api.routers import library
    from utils.auth import get_current_user

    seen = {}
    async def fake_ingest(path, user_id, filename):
        seen["path"], seen["filename"] = path, filename
        assert os.path.exists(path)
        return "user_u_library"

    class FakeTable:
        def insert(self, row): seen["row"] = row; return self
        def execute(self): return None
    class FakeSupabase:
        def table(self, name): return FakeTable()

    monkeypatch.setattr(library, "process_pdf_ingestion", fake_ingest)

    async def no_profile_check(user):
        return None
    monkeypatch.setattr(library, "ensure_profile", no_profile_check)
    monkeypatch.setattr(library, "get_supabase_client", lambda: FakeSupabase())
    app = FastAPI()
    app.include_router(library.router)
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()

    res = TestClient(app).post("/api/library/upload",
                               files={"file": ("../../evil.pdf", b"%PDF-1.4", "application/pdf")})

    assert res.status_code == 200
    assert os.path.dirname(os.path.realpath(seen["path"])) == os.path.realpath(tempfile.gettempdir())
    assert seen["filename"] == "evil.pdf"
    assert ".." not in seen["row"]["storage_path"]
    assert not os.path.exists(seen["path"])  # cleaned up

def test_upload_rejects_non_pdf(monkeypatch):
    from api.routers import library
    from utils.auth import get_current_user
    app = FastAPI()
    app.include_router(library.router)
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": "u"})()
    res = TestClient(app).post("/api/library/upload", files={"file": ("notes.txt", b"hi", "text/plain")})
    assert res.status_code == 400

def test_ensure_profile_creates_missing_profile_once(monkeypatch):
    import asyncio
    import utils.auth as auth

    calls = []
    class FakeQuery:
        def __init__(self, row, kwargs): calls.append((row, kwargs))
        def execute(self): return None
    class FakeTable:
        def upsert(self, row, **kwargs): return FakeQuery(row, kwargs)
    monkeypatch.setattr(auth, "supabase", type("SB", (), {"table": lambda self, name: FakeTable()})())
    monkeypatch.setattr(auth, "_profiles_ensured", set())

    user = type("U", (), {"id": "u-1", "email": "a@b.co", "user_metadata": {"full_name": "Ada"}})()
    asyncio.run(auth.ensure_profile(user))
    asyncio.run(auth.ensure_profile(user))  # cached: no second round trip

    assert calls == [({"id": "u-1", "email": "a@b.co", "full_name": "Ada"},
                      {"on_conflict": "id", "ignore_duplicates": True})]  # never overwrites an existing profile
