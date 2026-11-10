import asyncio
import json
import pytest
from langchain_core.messages import AIMessage

import agents.retriever
import search.planner, search.screening, search.providers, search.semantic_scholar
from search.planner import clean_query, normalise
from conftest import PLAN, PROFILE

STATE = {"topic": "x", "research_mode": "light", "research_plan": PLAN["research_plan"], "user_id": None}

def llm(answers, prompts=None):
    """A fake LLM answering by agent name; records (agent, system prompt, human message)."""
    async def fake(messages, agent_name=None, **kwargs):
        if prompts is not None:
            prompts.append((agent_name, messages[0].content, messages[-1].content))
        answer = answers.get(agent_name, "unparseable")
        return AIMessage(content=answer(messages) if callable(answer) else answer)
    return fake

@pytest.fixture
def searches(monkeypatch):
    """Providers that record which queries reached them."""
    calls = {"papers": [], "web": []}
    def provider(kind, name):
        def run(query, max_results=3):
            calls[kind].append(query)
            return [{"title": f"{name}: {query}", "url": f"https://{name}/{query}", "summary": "s", "source": name}]
        return run
    monkeypatch.setattr(search.providers, "search_openalex", provider("papers", "openalex"))
    monkeypatch.setattr(search.providers, "search_arxiv", provider("papers", "arxiv"))
    monkeypatch.setattr(search.providers, "search_core", lambda q, max_results=3: [])
    monkeypatch.setattr(search.providers, "search_semantic_scholar", lambda q, max_results=3: [])
    monkeypatch.setattr(search.providers, "search_web", provider("web", "web"))
    return calls

def use_llm(monkeypatch, answers, prompts=None):
    fake = llm(answers, prompts)
    monkeypatch.setattr(search.planner, "ainvoke_llm", fake)
    monkeypatch.setattr(search.screening, "ainvoke_llm", fake)

PLANNED = json.dumps([
    {"section": "Related Work", "need": "prior minimal GPTs", "kind": "papers", "query": '"GPT-2" language model 2019'},
    {"section": "Implementation", "need": "multi-GPU training", "kind": "web", "query": "PyTorch DistributedDataParallel"},
    {"section": "Results", "need": "our results", "kind": "none", "query": "anything"},
])

# ---- Planning ----------------------------------------------------------------------

def test_clean_query_keeps_keywords_only():
    assert clean_query('"FlashAttention" AND (GPU) 2023') == "FlashAttention GPU"
    assert len(clean_query("one two three four five six seven eight nine ten").split()) == 8

def test_normalise_validates_dedupes_and_caps():
    needs = normalise([
        {"section": "A", "need": "n", "kind": "papers", "query": "sparse attention"},
        {"section": "B", "need": "n", "kind": "papers", "query": "Sparse Attention"},   # duplicate
        {"section": "C", "need": "n", "kind": "blogs", "query": "graph neural nets"},   # unknown kind -> papers
        {"section": "D", "need": "n", "kind": "none", "query": "ignored"},
        {"section": "E", "need": "n", "kind": "web", "query": "over the cap"},
    ], max_needs=2)
    assert [(n["section"], n["kind"], n["query"]) for n in needs] == [
        ("A", "papers", "sparse attention"), ("C", "papers", "graph neural nets"), ("D", "none", "")]
    assert [n["id"] for n in needs] == [1, 2, 3]

def test_unparseable_plan_falls_back_to_the_topic(monkeypatch):
    use_llm(monkeypatch, {})
    needs = asyncio.run(search.planner.plan_searches({**STATE, "topic": "Sparse attention for long documents"}))
    assert {n["kind"] for n in needs} == {"papers", "web"}
    assert all(n["query"] == "Sparse attention for long documents" for n in needs)

def test_planner_sees_the_project(monkeypatch):
    prompts = []
    use_llm(monkeypatch, {"search_planning": PLANNED}, prompts)
    asyncio.run(search.planner.plan_searches({**STATE, "project_profile": {**PROFILE, "name": "octo/sparse"}}))
    human = prompts[0][2]
    assert "Block-sparse attention kernels" in human and "sparse attention; long-context transformers" in human

# ---- Retrieval -----------------------------------------------------------------------

def test_each_need_is_searched_only_where_it_can_be_answered(monkeypatch, searches):
    use_llm(monkeypatch, {"search_planning": PLANNED})
    out = asyncio.run(agents.retriever.retriever_node(STATE))

    assert searches["papers"] == ["GPT-2 language model"] * 2         # openalex + arxiv, cleaned query
    assert searches["web"] == ["PyTorch DistributedDataParallel"]     # web need never hits paper search
    assert {s["section"] for s in out["raw_sources"]} == {"Related Work", "Implementation"}  # "none" not searched
    plan = {n["section"]: n for n in out["search_plan"]}
    assert plan["Results"]["kind"] == "none" and plan["Related Work"]["sources"] == 2

def test_screening_drops_irrelevant_results(monkeypatch, searches):
    use_llm(monkeypatch, {"search_planning": PLANNED, "source_screening": '{"keep": [1, 3]}'})
    out = asyncio.run(agents.retriever.retriever_node(STATE))
    assert [s["title"] for s in out["raw_sources"]] == [
        "openalex: GPT-2 language model", "arxiv: GPT-2 language model"]

def test_thin_needs_are_searched_once_more_with_a_rewritten_query(monkeypatch, searches):
    prompts = []
    use_llm(monkeypatch, {
        "search_planning": PLANNED,
        "source_screening": lambda m: '{"keep": [1, 3]}' if "openalex" in m[-1].content else '{"keep": [1]}',
        "query_rewrite": '{"2": "PyTorch distributed training"}',
    }, prompts)
    out = asyncio.run(agents.retriever.retriever_node(STATE))

    assert searches["web"] == ["PyTorch DistributedDataParallel", "PyTorch distributed training"]
    assert [p[0] for p in prompts].count("query_rewrite") == 1  # one retry round, no more
    plan = {n["section"]: n for n in out["search_plan"]}
    assert plan["Implementation"]["retry_query"] == "PyTorch distributed training"
    assert plan["Implementation"]["sources"] == 1

def test_unreadable_screening_keeps_everything(monkeypatch, searches):
    use_llm(monkeypatch, {"search_planning": PLANNED, "source_screening": "I think they're all fine"})
    out = asyncio.run(agents.retriever.retriever_node(STATE))
    assert len(out["raw_sources"]) == 3

def test_repository_is_cited_once_even_when_the_web_finds_it(monkeypatch, searches):
    monkeypatch.setattr(search.providers, "search_web", lambda q, max_results=3: [
        {"title": "octo/sparse", "url": "https://github.com/octo/sparse", "summary": "s", "source": "Web"}])
    use_llm(monkeypatch, {"search_planning": PLANNED})
    profile = {**PROFILE, "name": "octo/sparse", "url": "https://github.com/octo/sparse"}
    out = asyncio.run(agents.retriever.retriever_node({**STATE, "project_profile": profile}))
    urls = [s["url"] for s in out["raw_sources"]]
    assert urls.count("https://github.com/octo/sparse") == 1 and urls[0] == "https://github.com/octo/sparse"

def test_the_same_paper_from_two_providers_is_kept_once(monkeypatch, searches):
    same = lambda q, max_results=3: [{"title": "StableMask: Refining Causal Masking", "url": "https://core/x", "summary": "s", "source": "CORE"}]
    monkeypatch.setattr(search.providers, "search_openalex", lambda q, max_results=3: [
        {"title": "StableMask: refining causal masking.", "url": "https://openalex/x", "summary": "s", "source": "OpenAlex"}])
    monkeypatch.setattr(search.providers, "search_core", same)
    use_llm(monkeypatch, {"search_planning": PLANNED})
    titles = [s["title"] for s in asyncio.run(agents.retriever.retriever_node(STATE))["raw_sources"]]
    assert sum("stablemask" in t.lower() for t in titles) == 1

def test_every_section_is_covered_before_any_gets_a_second_search():
    raw = [{"section": "Related Work", "kind": "papers", "query": f"related {i}"} for i in range(3)] + \
          [{"section": "Training", "kind": "web", "query": "PyTorch DDP"},
           {"section": "Architecture", "kind": "papers", "query": "FlashAttention"}]
    needs = normalise(raw, max_needs=3)
    assert [n["section"] for n in needs] == ["Related Work", "Training", "Architecture"]

# ---- Semantic Scholar ----------------------------------------------------------------

S2_PAPER = {"title": "Attention Is All You Need", "abstract": "The dominant sequence transduction models...",
            "year": 2017, "citationCount": 150000, "url": "https://www.semanticscholar.org/paper/abc",
            "externalIds": {"ArXiv": "1706.03762", "DOI": "10.5555/x"}, "authors": [{"name": "Ashish Vaswani"}]}

def test_semantic_scholar_papers_link_to_the_most_readable_copy():
    source = search.semantic_scholar.s2_source(S2_PAPER)
    assert source["url"] == "https://arxiv.org/abs/1706.03762"  # arXiv before DOI before S2
    assert source["citations"] == 150000 and source["authors"] == ["Ashish Vaswani"]
    no_arxiv = search.semantic_scholar.s2_source({**S2_PAPER, "externalIds": {"DOI": "10.5555/x"}})
    assert no_arxiv["url"] == "https://doi.org/10.5555/x"
    neither = search.semantic_scholar.s2_source({**S2_PAPER, "externalIds": {}})
    assert neither["url"] == "https://www.semanticscholar.org/paper/abc"

def test_semantic_scholar_is_throttled_and_retries_once_when_rate_limited(monkeypatch):
    class Response:
        def __init__(self, status): self.status_code = status
        def json(self): return {"data": [S2_PAPER]}
    statuses = [429, 200]
    sleeps = []
    monkeypatch.setattr(search.semantic_scholar.requests, "get", lambda *a, **k: Response(statuses.pop(0)))
    monkeypatch.setattr(search.semantic_scholar.time, "sleep", sleeps.append)
    monkeypatch.setattr(search.semantic_scholar, "_s2_last_call", 0.0)
    monkeypatch.setattr(search.semantic_scholar, "_s2_skip_until", 0.0)

    found = search.semantic_scholar.search_semantic_scholar("attention is all you need")
    assert [s["title"] for s in found] == ["Attention Is All You Need"]
    assert 2 in sleeps  # backed off after the 429

def test_semantic_scholar_ranks_first_among_paper_searches():
    assert search.providers.searchers("papers")[0] is search.providers.search_semantic_scholar
    assert search.providers.search_semantic_scholar not in search.providers.searchers("web")

def test_screening_sees_citation_counts(monkeypatch):
    prompts = []
    use_llm(monkeypatch, {}, prompts)
    need = {"need": "transformer architecture", "query": "q"}
    asyncio.run(search.screening.screen([(need, {"title": "Attention Is All You Need", "citations": 150000, "summary": "s"})]))
    assert "Attention Is All You Need (cited by 150,000)" in prompts[0][2]

def test_semantic_scholar_is_skipped_for_a_while_after_repeated_rate_limits(monkeypatch):
    calls = []
    class Refused:
        status_code = 429
    monkeypatch.setattr(search.semantic_scholar.requests, "get", lambda *a, **k: calls.append(1) or Refused())
    monkeypatch.setattr(search.semantic_scholar.time, "sleep", lambda s: None)
    monkeypatch.setattr(search.semantic_scholar, "_s2_last_call", 0.0)
    monkeypatch.setattr(search.semantic_scholar, "_s2_skip_until", 0.0)

    assert search.semantic_scholar.search_semantic_scholar("q1") == []
    assert len(calls) == 2  # tried, retried once
    assert search.semantic_scholar.search_semantic_scholar("q2") == []
    assert len(calls) == 2  # cooling off: not called again

# ---- arXiv ---------------------------------------------------------------------------

def test_arxiv_relevance_search_requires_every_keyword_first(monkeypatch):
    urls = []
    monkeypatch.setattr(search.providers, "_fetch_arxiv", lambda url, q: urls.append(url) or [{"title": "hit"}])
    search.providers.search_arxiv("Attention Is All You Need")
    assert len(urls) == 1
    assert "search_query=all:Attention%20AND%20all:Need&" in urls[0]  # "Is All You" are ignored by arXiv
    assert urls[0].endswith("&sortBy=relevance")

def test_arxiv_relaxes_to_leading_keywords_then_any_word(monkeypatch):
    urls = []
    monkeypatch.setattr(search.providers, "_fetch_arxiv", lambda url, q: urls.append(url) or ([{"title": "hit"}] if len(urls) == 3 else []))
    found = search.providers.search_arxiv("Attention Is All You Need causal self-attention models")
    assert found == [{"title": "hit"}] and len(urls) == 3
    assert urls[0].count("%20AND%20") == 5                      # every keyword (6, stopwords dropped)
    assert "all:Attention%20AND%20all:Need%20AND%20all:causal%20AND%20all:self&" in urls[1]  # the leading four
    assert "AND" not in urls[2]                                  # any word

def test_arxiv_short_query_is_not_tried_twice(monkeypatch):
    urls = []
    monkeypatch.setattr(search.providers, "_fetch_arxiv", lambda url, q: urls.append(url) or [])
    search.providers.search_arxiv("FlashAttention")
    assert len(urls) == 2  # all keywords (= leading keywords), then any word

def test_arxiv_newest_first_still_sorts_by_date(monkeypatch):
    urls = []
    monkeypatch.setattr(search.providers, "_fetch_arxiv", lambda url, q: urls.append(url) or [{"title": "hit"}])
    search.providers.search_arxiv("sparse attention", newest_first=True)
    assert urls[0].endswith("&sortBy=submittedDate&sortOrder=descending")
