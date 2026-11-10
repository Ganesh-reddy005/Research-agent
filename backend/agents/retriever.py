"""Retriever: plan the searches the paper needs, run each where it can be answered, keep the
relevant results, and search once more for needs that found too little."""
import re
import asyncio
from itertools import zip_longest
from utils.events import report_progress
from agents.project_context import project_source
from search import providers
from search.planner import plan_searches
from search.screening import screen, rewrite_queries

RESULTS_PER_PROVIDER = {"light": 3, "deep": 5}
MIN_SOURCES_PER_NEED = 2

def interleave(lists):
    """Best of each list first, then second-best, ... so early items span every list."""
    return [item for rank in zip_longest(*lists) for item in rank if item]

async def run_need(need, user_id, per_provider) -> list[dict]:
    """One need's results, alternating between its providers. Searches run in worker threads so the
    blocking HTTP clients never stall the event loop; gather() keeps the order deterministic."""
    calls = [asyncio.to_thread(search, need["query"], max_results=per_provider) for search in providers.searchers(need["kind"])]
    if user_id:
        calls.append(asyncio.to_thread(providers.search_private_library, need["query"], user_id, max_results=per_provider))
    lists = []
    for res in await asyncio.gather(*calls, return_exceptions=True):
        if isinstance(res, Exception):
            print(f"Search failed for '{need['query']}': {res}")
        elif isinstance(res, list):
            lists.append(res)
    return interleave(lists)

def title_key(source) -> str:
    """The same paper from two providers has different URLs but the same title."""
    return "title:" + re.sub(r"[^a-z0-9]+", " ", (source.get("title") or "").lower()).strip()

async def search_needs(needs, user_id, per_provider, seen) -> list[tuple[dict, dict]]:
    """(need, source) pairs across all needs, interleaved; anything already in seen (by URL or by
    title) is skipped, and what's kept is added to it."""
    found = await asyncio.gather(*(run_need(n, user_id, per_provider) for n in needs))
    pairs = []
    for need, source in interleave([[(n, s) for s in sources] for n, sources in zip(needs, found)]):
        keys = {source.get("url"), title_key(source)} - {None, "title:"}
        if source.get("url") and not keys & seen:
            seen |= keys
            pairs.append((need, source))
    return pairs

def describe_plan(needs) -> str:
    papers = sum(n["kind"] == "papers" for n in needs)
    web = sum(n["kind"] == "web" for n in needs)
    covered = sum(n["kind"] == "none" for n in needs)
    text = f"Planned {papers + web} searches: {papers} for papers, {web} on the web"
    return text + (f"; {covered} covered without searching" if covered else "")

async def retry_thin_needs(searchable, kept, user_id, per_provider, seen):
    """One more search, with a rewritten query, for each need that kept too few sources."""
    counts = {n["id"]: 0 for n in searchable}
    for need, _ in kept:
        counts[need["id"]] += 1
    thin = [n for n in searchable if counts[n["id"]] < MIN_SOURCES_PER_NEED]
    rewritten = await rewrite_queries(thin)
    if not rewritten:
        return []
    retry = [{**n, "query": rewritten[n["id"]]} for n in thin if n["id"] in rewritten]
    await report_progress(f"Searching again for {len(retry)} topic{'s' if len(retry) > 1 else ''} with too few sources")
    for need in retry:
        next(n for n in searchable if n["id"] == need["id"])["retry_query"] = need["query"]
    return await screen(await search_needs(retry, user_id, per_provider, seen))

def search_summary(needs, kept) -> list[dict]:
    counts = {}
    for need, _ in kept:
        counts[need["id"]] = counts.get(need["id"], 0) + 1
    return [{**n, "sources": counts.get(n["id"], 0)} for n in needs]

async def retriever_node(state):
    print("--- RETRIEVER AGENT ---")
    per_provider = RESULTS_PER_PROVIDER.get(state.get("research_mode", "deep"), RESULTS_PER_PROVIDER["deep"])
    user_id = state.get("user_id")

    needs = await plan_searches(state)
    searchable = [n for n in needs if n["kind"] != "none"]
    await report_progress(describe_plan(needs))

    profile = state.get("project_profile")
    project_url = (profile or {}).get("url")
    seen = {project_url} if project_url else set()  # the repository is already source [1]
    found = await search_needs(searchable, user_id, per_provider, seen)
    await report_progress(f"Checking {len(found)} results for relevance")
    kept = await screen(found)
    kept += await retry_thin_needs(searchable, kept, user_id, per_provider, seen)

    sources = [{**source, "need": need["need"], "section": need["section"]} for need, source in kept]
    # A project paper cites its own repository first, as [1]
    if project_url:
        sources.insert(0, project_source(profile))

    await report_progress(f"Kept {len(kept)} relevant sources")
    return {"raw_sources": sources, "search_plan": search_summary(needs, kept), "current_step": "retriever"}
