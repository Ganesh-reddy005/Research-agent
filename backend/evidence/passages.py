"""Evidence passages for writing one part of a paper.

A passage is (text, url, title). Its url decides its citation number, so only passages whose url
is in raw_sources can be cited. Each kind of evidence is one provider below; a new kind (e.g.
experiment runs) is another provider added to section_evidence."""
import asyncio

from agents.project_context import is_project_paper, is_project_source
from utils.vectorstore import collection_exists, get_vector_store, qdrant_configured, repo_collection, research_collection

Passage = tuple[str, str, str]


async def _search(collection: str, query: str, k: int) -> list[Passage]:
    """Diverse passages (MMR) rather than several from one document."""
    if not qdrant_configured() or not await asyncio.to_thread(collection_exists, collection):
        return []
    results = await get_vector_store(collection).amax_marginal_relevance_search(query, k=k, fetch_k=k * 4)
    return [(r.page_content, r.metadata.get("url"), r.metadata.get("title")) for r in results]


async def literature_passages(state, query: str, k: int) -> list[Passage]:
    thread_id = state.get("thread_id", "default_thread")
    found = await _search(research_collection(thread_id), query, k)
    if found:
        return found
    # Nothing indexed: fall back to the abstracts of the retrieved sources
    sources = [s for s in state.get("raw_sources", []) if not is_project_source(s)]
    return [(s.get("summary", ""), s.get("url"), s.get("title")) for s in sources[:10]]


async def project_passages(state, query: str, k: int) -> list[Passage]:
    if not is_project_paper(state):
        return []
    profile = state["project_profile"]
    found = await _search(repo_collection(state.get("thread_id", "default_thread")), query, k)
    if found:
        return found
    # Code not indexed: the profile itself is the project evidence
    summary = f"{profile.get('summary', '')}\nApproach: {profile.get('approach', '')}"
    return [(summary, profile.get("url"), profile.get("name"))]


async def section_evidence(state, query: str, k: int = 8) -> list[Passage]:
    """About k passages: project code first (a project paper's claims about itself), then the literature."""
    project, literature = await asyncio.gather(
        project_passages(state, query, k=max(5, k // 2)),
        literature_passages(state, query, k=k - 2 if is_project_paper(state) else k),
    )
    return project + literature
