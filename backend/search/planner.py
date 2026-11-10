"""What to search for: the information each section of the paper needs from outside sources,
one short query per need, and whether papers or the web can answer it.

A need is {"id", "section", "need", "kind", "query"}; kind is "papers", "web" or "none" (the
project itself or the paper's own argument covers it, so nothing is searched)."""
import json
import re
from itertools import zip_longest
from langchain_core.messages import HumanMessage, SystemMessage
from agents.project_context import project_context
from utils.llm import ainvoke_llm

KINDS = {"papers", "web", "none"}
MAX_QUERY_WORDS = 8  # the prompt asks for 2-6; anything longer is cut, not rejected
# Searches per paper, by research mode
MAX_NEEDS = {"light": 6, "deep": 12}

SYSTEM_PROMPT = """You plan the searches for a research paper. Read the plan (and the project, if the paper
presents one), work out what each section needs to learn from OUTSIDE sources, and write one search per need.

kind:
- "papers": academic knowledge (prior methods, theory, models, benchmarks, related work). Searched on arXiv, OpenAlex and CORE.
- "web": practical knowledge (libraries, frameworks, tools, documentation, dataset homepages, industry practice). Searched on the web.
- "none": the section is covered by the authors' own project or the paper's own argument (implementation details,
  the project's results, the conclusion). Nothing is searched.

query: 2-6 keywords, as you would type into Google Scholar or Google. Lead with specific names: methods, models,
datasets, tools. No filler ("analysis of", "a study on", "impact of", "overview"), no years, no quotes or operators.
When the need is a specific well-known paper, use the key words of its title, so the original is found rather
than follow-ups (e.g. "FlashAttention fast memory-efficient exact attention").
Good: "GPT-2 language model", "OpenWebText dataset", "PyTorch DistributedDataParallel".
Bad: "a comprehensive analysis of minimal transformer implementations for education".

Cover every section first: give each one at least one need ("none" if it needs no outside sources), then spend
what remains of the budget where the paper needs the most support. Libraries, frameworks and training tooling
are "web" needs. One need per distinct piece of information, no duplicates.
At most {max_needs} needs that are not "none".
Return STRICTLY a JSON array: [{{"section": "Section title", "need": "what it must learn", "kind": "papers", "query": "..."}}]"""

_YEAR = re.compile(r"\b(19|20)\d\d\b")
_OPERATORS = re.compile(r'["“”\'()]|\b(AND|OR|NOT)\b')


def clean_query(query: str) -> str:
    """Search-engine-ready keywords: no quotes, operators or years, at most MAX_QUERY_WORDS words."""
    text = _YEAR.sub(" ", _OPERATORS.sub(" ", str(query)))
    return " ".join(text.split()[:MAX_QUERY_WORDS])


def _parse(content: str) -> list:
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []


def sections_first(raw: list) -> list:
    """Every section's first need before any section's second, so the cap never leaves a section
    unsearched while another gets three searches."""
    by_section = {}
    for item in raw:
        by_section.setdefault(str(item.get("section", "")), []).append(item)
    return [item for rank in zip_longest(*by_section.values()) for item in rank if item]


def normalise(raw: list, max_needs: int) -> list[dict]:
    """Valid, de-duplicated needs with ids, covering sections before deepening them; searchable needs
    capped at max_needs."""
    needs, seen, searchable = [], set(), 0
    for item in sections_first(raw):
        kind = item.get("kind") if item.get("kind") in KINDS else "papers"
        query = clean_query(item.get("query", ""))
        if kind != "none":
            key = (kind, query.lower())  # the same query may serve papers and the web
            if not query or key in seen or searchable >= max_needs:
                continue
            seen.add(key)
            searchable += 1
        needs.append({"id": len(needs) + 1, "section": str(item.get("section", "")), "need": str(item.get("need", "")),
                      "kind": kind, "query": query if kind != "none" else ""})
    return needs


def fallback_needs(topic: str) -> list[dict]:
    """When the plan can't be parsed: the topic itself, on papers and the web."""
    query = clean_query(topic)
    return normalise([{"need": topic, "kind": "papers", "query": query},
                      {"need": topic, "kind": "web", "query": query}], max_needs=2)


async def plan_searches(state) -> list[dict]:
    max_needs = MAX_NEEDS.get(state.get("research_mode", "deep"), MAX_NEEDS["deep"])
    sections = "\n".join(f"- {s.get('title')}: {s.get('description')}"
                         for s in (state.get("research_plan") or {}).get("sections", []))
    human = f"Topic: {state.get('topic')}\n\nPlan sections:\n{sections}"
    project = project_context(state)
    if project:
        human += f"\n\n{project}\n\nSuggested related-work queries: {'; '.join(state['project_profile'].get('related_work_queries', []))}"
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(max_needs=max_needs)), HumanMessage(content=human)]
    response = await ainvoke_llm(messages, agent_name="search_planning")
    needs = normalise(_parse(response.content), max_needs)
    return needs if any(n["kind"] != "none" for n in needs) else fallback_needs(state.get("topic", ""))
