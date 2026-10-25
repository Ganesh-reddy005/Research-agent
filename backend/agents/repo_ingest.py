import asyncio
from utils.events import report_progress
from utils.vectorstore import qdrant_configured, repo_collection
from repo.github import parse_github_url, fetch_repo
from repo.filetypes import should_read
from repo.scanner import build_snapshot
from repo.profiler import profile_repo
from repo.indexing import index_repo

async def index_code(state, snapshot, repo) -> int:
    """Best effort: without the index the writer cites the project from its profile instead."""
    if not qdrant_configured():
        return 0
    await report_progress("Indexing the code so the paper can cite it")
    collection = repo_collection(state.get("thread_id", "default_thread"))
    try:
        return await asyncio.to_thread(index_repo, snapshot, collection, repo.full_name, repo.url)
    except Exception as e:
        print(f"Indexing {repo.full_name} failed, continuing without code passages: {e}")
        await report_progress("Couldn't index the code; the paper will cite the project summary instead")
        return 0

async def repo_ingest_node(state):
    """Read the repository a project paper is about: fetch, scan, profile, and index its code."""
    print("--- REPO INGEST AGENT ---")
    repo = parse_github_url(state["repo_url"])

    await report_progress(f"Downloading {repo.full_name} from GitHub")
    fetched = await fetch_repo(repo, include=should_read)
    snapshot = await asyncio.to_thread(build_snapshot, fetched.files)
    if not snapshot.files:
        raise ValueError(f"{repo.full_name} has no source files Lume can read.")

    await report_progress(f"Read {len(snapshot.files)} files ({snapshot.total_lines:,} lines of code). Working out what the project does")
    profile = await profile_repo(fetched, snapshot, state.get("project_notes", ""))

    indexed = await index_code(state, snapshot, repo)
    return {
        "project_profile": {**profile, "indexed_chunks": indexed},
        "topic": state.get("topic") or profile.get("title") or repo.full_name,
        "current_step": "repo_ingest",
    }
