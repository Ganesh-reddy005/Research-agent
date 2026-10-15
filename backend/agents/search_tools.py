"""Live search tools the brainstorm agent can call: the web (Tavily), arXiv and OpenAlex."""
import os
import asyncio
from langchain_core.tools import tool
from tavily import TavilyClient
from agents.retriever import search_arxiv, search_openalex

RESULTS_PER_SEARCH = 5

def _search_web(query, max_results=RESULTS_PER_SEARCH):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    res = TavilyClient(api_key=key).search(query=query, search_depth="basic", max_results=max_results)
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "summary": r.get("content", ""), "source": "Web"}
            for r in res.get("results", [])]

_SEARCHERS = {
    "web_search": _search_web,
    "search_arxiv": search_arxiv,
    "search_openalex": search_openalex,
}

async def run_search(tool_name: str, args: dict) -> list:
    """Run one search off the event loop; unknown tools or failures return no results."""
    searcher = _SEARCHERS.get(tool_name)
    query = (args or {}).get("query", "")
    if not searcher or not query:
        return []
    kwargs = {"max_results": RESULTS_PER_SEARCH}
    if tool_name == "search_arxiv" and args.get("newest_first"):
        kwargs["newest_first"] = True
    try:
        return await asyncio.to_thread(searcher, query, **kwargs)
    except Exception as e:
        print(f"{tool_name} failed for '{query}': {e}")
        return []

def format_results(sources: list) -> str:
    """Numbered results for the model to read and cite as [n]."""
    if not sources:
        return "No results found."
    blocks = []
    for s in sources:
        year = f", {s['year']}" if s.get("year") else ""
        blocks.append(f"[{s['n']}] {s['title']} ({s['source']}{year})\nURL: {s['url']}\n{(s.get('summary') or '')[:700]}")
    return "\n\n".join(blocks)

def public_source(s: dict) -> dict:
    """What the browser needs to show a source (no long abstracts)."""
    return {k: s.get(k) for k in ("n", "title", "url", "source", "year")}

# Schemas only: the brainstorm graph's tools node executes searches itself so it can
# number sources across a turn and report progress to the UI.
@tool
def web_search(query: str) -> str:
    """Search the live web. Use for recent news, releases, documentation, benchmarks, leaderboards or anything time-sensitive."""
    raise NotImplementedError

@tool("search_arxiv")
def search_arxiv_tool(query: str, newest_first: bool = False) -> str:
    """Search arXiv preprints in CS, ML, physics and maths. Set newest_first=true when the user wants the
    latest or most recent work: results are then sorted by submission date instead of relevance.
    Put only topic keywords in the query, never years or dates."""
    raise NotImplementedError

@tool("search_openalex")
def search_openalex_tool(query: str) -> str:
    """Search OpenAlex, a catalogue of 250M+ published scholarly works. Use for peer-reviewed papers and well-established findings."""
    raise NotImplementedError

SEARCH_TOOLS = [web_search, search_arxiv_tool, search_openalex_tool]
