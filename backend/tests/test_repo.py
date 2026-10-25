import asyncio
import io
import json
import tarfile
import httpx
import pytest

import agents.repo_ingest
from repo.github import FetchedRepo, RepoError, RepoRef, parse_github_url, read_archive, is_transient, _check
from repo.filetypes import should_read
from repo.scanner import build_snapshot, key_files
from repo.indexing import chunk_repo
from conftest import PROFILE

# ---- Parsing links ---------------------------------------------------------------

@pytest.mark.parametrize("link, expected", [
    ("https://github.com/octo/sparse-attn", RepoRef("octo", "sparse-attn")),
    ("github.com/octo/sparse-attn.git", RepoRef("octo", "sparse-attn")),
    ("https://github.com/octo/sparse-attn/tree/dev", RepoRef("octo", "sparse-attn", "dev")),
    ("https://github.com/octo/sparse-attn/tree/feature/x/", RepoRef("octo", "sparse-attn", "feature/x")),
    ("https://github.com/octo/sparse-attn/blob/main/src/kernel.py", RepoRef("octo", "sparse-attn")),
    ("  octo/sparse_attn.v2  ", RepoRef("octo", "sparse_attn.v2")),
])
def test_parse_github_url(link, expected):
    assert parse_github_url(link) == expected

@pytest.mark.parametrize("link", ["https://gitlab.com/octo/x", "github.com/octo", "not a link", ""])
def test_parse_github_url_rejects_other_links(link):
    with pytest.raises(RepoError):
        parse_github_url(link)

def test_missing_repository_has_a_readable_error_and_is_not_retried():
    request = httpx.Request("GET", "https://api.github.com/repos/octo/x")
    with pytest.raises(RepoError, match="Couldn't find octo/x"):
        _check(httpx.Response(404, request=request), RepoRef("octo", "x"))
    assert not is_transient(RepoError("too large"))
    assert is_transient(httpx.ConnectError("dns"))
    assert is_transient(httpx.HTTPStatusError("x", request=request, response=httpx.Response(502, request=request)))

# ---- Reading the archive ---------------------------------------------------------

def tarball(files: dict, links=()) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path, data in files.items():
            info = tarfile.TarInfo(f"octo-sparse-abc1234/{path}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        for path in links:
            info = tarfile.TarInfo(f"octo-sparse-abc1234/{path}")
            info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
            tar.addfile(info)
    return buffer.getvalue()

NOTEBOOK = json.dumps({"cells": [{"cell_type": "markdown", "source": ["# Train"]},
                                 {"cell_type": "code", "source": ["model.fit(x)"], "outputs": ["huge"]}]}).encode()

REPO_FILES = {
    "README.md": b"# Sparse attention\nSee src/kernel.py for the kernel.",
    "requirements.txt": b"torch\nnumpy",
    "src/kernel.py": b"def sparse_matmul(a, b):\n    return a @ b\n",
    "src/utils_helpers.py": b"x = 1\n" * 50,
    "tests/test_kernel.py": b"def test_kernel():\n    assert True\n",
    "notebooks/train.ipynb": NOTEBOOK,
    "config.yaml": b"lr: 0.1",
    "node_modules/lib/index.js": b"module.exports = 1",
    "assets/logo.png": b"\x89PNG\x00\x00",
    "package-lock.json": b"{}",
    "../escape.py": b"print('outside')",
}

def test_read_archive_reads_only_safe_relevant_files():
    files, skipped, commit = read_archive(tarball(REPO_FILES, links=["src/link.py"]), should_read)
    paths = {path for path, _ in files}
    assert paths == {"README.md", "requirements.txt", "src/kernel.py", "src/utils_helpers.py",
                     "tests/test_kernel.py", "notebooks/train.ipynb", "config.yaml"}
    assert skipped == 3  # node_modules, png, lockfile; the link and '../' are never considered
    assert commit == "abc1234"

def test_read_archive_rejects_garbage():
    with pytest.raises(RepoError):
        read_archive(b"not a tarball", should_read)

# ---- Snapshot ----------------------------------------------------------------------

def snapshot():
    files, _, _ = read_archive(tarball(REPO_FILES), should_read)
    return build_snapshot(files)

def test_snapshot_finds_readme_manifests_languages_and_notebook_cells():
    snap = snapshot()
    assert snap.readme.startswith("# Sparse attention")
    assert set(snap.manifests) == {"requirements.txt"}
    assert set(snap.languages) == {"Python", "Jupyter Notebook"}
    notebook = next(f for f in snap.files if f.path.endswith(".ipynb"))
    assert "model.fit(x)" in notebook.text and "huge" not in notebook.text

def test_key_files_rank_core_code_first_and_skip_tests():
    picked = [path for path, _ in key_files(snapshot())]
    assert picked[0] == "src/kernel.py"  # mentioned in the README
    assert "tests/test_kernel.py" not in picked

def test_code_chunks_are_cited_as_the_repository():
    texts, metadatas = chunk_repo(snapshot(), "octo/sparse", "https://github.com/octo/sparse")
    assert texts and all(m["url"] == "https://github.com/octo/sparse" for m in metadatas)
    kernel = next(t for t, m in zip(texts, metadatas) if m["path"] == "src/kernel.py")
    assert kernel.startswith("File: src/kernel.py")
    assert not any(m["path"] == "config.yaml" for m in metadatas)

# ---- The repository path through the graph -------------------------------------------

@pytest.fixture
def offline_repo(offline_graph, monkeypatch):
    files, _, _ = read_archive(tarball(REPO_FILES), should_read)

    async def fake_fetch(repo, include, token=None):
        return FetchedRepo(repo=repo, branch="main", commit="abc1234", description="Sparse attention", files=files)
    monkeypatch.setattr(agents.repo_ingest, "fetch_repo", fake_fetch)
    return offline_graph

def test_repo_paper_runs_end_to_end(offline_repo):
    graph, _ = offline_repo
    config = {"configurable": {"thread_id": "repo-1"}}
    state = {"topic": "", "repo_url": "https://github.com/octo/sparse", "project_notes": "My course project",
             "research_mode": "light", "thread_id": "repo-1", "user_id": "u"}

    async def run():
        await graph.ainvoke(state, config)
        paused = await graph.aget_state(config)
        for _ in range(3):
            await graph.ainvoke(None, config)
        return paused, (await graph.aget_state(config)).values

    paused, final = asyncio.run(run())

    assert paused.next == ("planning",)  # read the repository, then asked its questions
    profile = paused.values["project_profile"]
    assert profile["name"] == "octo/sparse" and profile["commit"] == "abc1234"
    assert paused.values["topic"] == PROFILE["title"]

    assert final["raw_sources"][0]["url"] == "https://github.com/octo/sparse"  # the repository is [1]
    assert final["final_report"] == "Final paper citing [1]."
    assert final["citation_audit_log"]["unique_sources_cited"] == 1

def test_topic_paper_skips_repo_ingest(offline_graph):
    graph, _ = offline_graph
    config = {"configurable": {"thread_id": "t-plain"}}
    state = {"topic": "x", "research_mode": "light", "thread_id": "t-plain", "user_id": "u"}

    async def run():
        await graph.ainvoke(state, config)
        for _ in range(3):
            await graph.ainvoke(None, config)
        return (await graph.aget_state(config)).values

    final = asyncio.run(run())
    assert "project_profile" not in final
    assert final["final_report"] == "Final paper citing [1]."

def test_clarification_asks_project_questions_for_a_repo(monkeypatch):
    import agents.clarification
    from langchain_core.messages import AIMessage
    prompts = []
    async def capture(messages, **kwargs):
        prompts.append((messages[0].content, messages[1].content))
        return AIMessage(content='[{"id": "1", "question": "Which course is this for?"}]')
    monkeypatch.setattr(agents.clarification, "ainvoke_llm", capture)

    asyncio.run(agents.clarification.clarification_node({"topic": "t", "project_profile": {**PROFILE, "name": "octo/sparse"}}))
    system, human = prompts[0]
    assert "only the authors can answer" in system.lower()
    assert "Block-sparse attention kernels" in human

def test_repo_ingest_survives_a_vector_store_outage(offline_repo, monkeypatch):
    def down(*args):
        raise ConnectionResetError("Connection reset by peer")
    monkeypatch.setattr(agents.repo_ingest, "qdrant_configured", lambda: True)
    monkeypatch.setattr(agents.repo_ingest, "index_repo", down)

    out = asyncio.run(agents.repo_ingest.repo_ingest_node({"repo_url": "octo/sparse", "thread_id": "t"}))
    assert out["project_profile"]["indexed_chunks"] == 0
    assert out["topic"] == PROFILE["title"]
