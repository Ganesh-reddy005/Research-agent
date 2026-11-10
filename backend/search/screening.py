"""Which search results are worth reading, and better queries for needs that found too little.

Both are one LLM call over the whole batch, and both fail open: if the model's answer can't be
parsed, every result is kept and no query is rewritten."""
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from search.planner import clean_query
from utils.llm import ainvoke_llm

MAX_SCREENED = 120  # results per screening call; beyond this they are kept unscreened
SUMMARY_CHARS = 220

SCREEN_PROMPT = """You screen search results for a research paper. Each numbered result was found for the need shown.
Keep a result if a careful author could cite it for that need: it addresses the need, and it is substantive
(a paper, official documentation or a technical article). Original and widely used works are the best keeps.
Drop results that merely share keywords (the same technique applied to an unrelated domain, language or hardware),
unrelated namesakes, listicles, ads, course or product landing pages.
Return STRICTLY a JSON object: {"keep": [numbers of the results to keep]}"""

REWRITE_PROMPT = """These searches for a research paper found too few useful results. For each, write a better query:
2-6 keywords, MORE specific rather than more generic: the standard name of the method, model, dataset or tool,
or the key title words of the best-known paper on it. Never a generic phrase like "language model training".
No filler, years, quotes or operators.
Return STRICTLY a JSON object mapping each id to its new query: {"3": "new query"}"""


def _json_object(content: str) -> dict:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _cited(source) -> str:
    """Citation count, where the provider has one: it tells a landmark paper from a minor one."""
    return f" (cited by {source['citations']:,})" if isinstance(source.get("citations"), int) else ""


async def screen(results: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    """results are (need, source) pairs, in order; returns the relevant ones, order kept."""
    if not results:
        return []
    batch, rest = results[:MAX_SCREENED], results[MAX_SCREENED:]
    lines = [f"[{i}] need: {need['need'] or need['query']} | {src.get('title', '')}{_cited(src)} | {src.get('summary', '')[:SUMMARY_CHARS]}"
             for i, (need, src) in enumerate(batch, start=1)]
    messages = [SystemMessage(content=SCREEN_PROMPT), HumanMessage(content="\n".join(lines))]
    response = await ainvoke_llm(messages, agent_name="source_screening")
    keep = _json_object(response.content).get("keep")
    if not isinstance(keep, list):
        return results  # unreadable answer: keep everything rather than lose good sources
    wanted = {int(k) for k in keep if str(k).isdigit()}
    return [pair for i, pair in enumerate(batch, start=1) if i in wanted] + rest


async def rewrite_queries(needs: list[dict]) -> dict[int, str]:
    """{need id: new query} for needs that found too little; unchanged or empty queries are left out."""
    if not needs:
        return {}
    lines = [f"{n['id']}: need: {n['need']} | query that found too little: {n['query']} | kind: {n['kind']}" for n in needs]
    messages = [SystemMessage(content=REWRITE_PROMPT), HumanMessage(content="\n".join(lines))]
    response = await ainvoke_llm(messages, agent_name="query_rewrite")
    old = {n["id"]: n["query"].lower() for n in needs}
    rewritten = {}
    for key, query in _json_object(response.content).items():
        need_id, query = int(key) if str(key).isdigit() else None, clean_query(query)
        if need_id in old and query and query.lower() != old[need_id]:
            rewritten[need_id] = query
    return rewritten
