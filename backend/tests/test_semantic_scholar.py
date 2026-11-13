"""Semantic Scholar provider: source links, throttling and intermittent rate limits."""
import search.semantic_scholar

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

def s2_reset(monkeypatch, statuses, calls=None):
    class Response:
        def __init__(self, status): self.status_code = status
        def json(self): return {"data": [S2_PAPER]}
    monkeypatch.setattr(search.semantic_scholar.requests, "get",
                        lambda *a, **k: (calls.append(1) if calls is not None else None) or Response(statuses.pop(0)))
    monkeypatch.setattr(search.semantic_scholar.time, "sleep", lambda s: None)
    for name, value in [("_s2_last_call", 0.0), ("_s2_skip_until", 0.0), ("_s2_failed_calls", 0)]:
        monkeypatch.setattr(search.semantic_scholar, name, value)

def test_semantic_scholar_retries_intermittent_rate_limits(monkeypatch):
    s2_reset(monkeypatch, [429, 429, 429, 200])  # refusals come and go, even at 1 request a second
    found = search.semantic_scholar.search_semantic_scholar("attention is all you need")
    assert [s["title"] for s in found] == ["Attention Is All You Need"]

def test_semantic_scholar_is_skipped_only_after_several_searches_fail_outright(monkeypatch):
    attempts, calls = search.semantic_scholar.S2_ATTEMPTS, []
    s2_reset(monkeypatch, [429] * attempts * 3 + [200], calls)
    for q in ["q1", "q2"]:
        assert search.semantic_scholar.search_semantic_scholar(q) == []
    assert len(calls) == 2 * attempts  # each search tried every attempt; not skipped yet
    assert search.semantic_scholar.search_semantic_scholar("q3") == []  # third failure in a row
    assert search.semantic_scholar.search_semantic_scholar("q4") == []
    assert len(calls) == 3 * attempts  # cooling off: q4 never called

def test_a_successful_search_resets_the_failure_count(monkeypatch):
    attempts = search.semantic_scholar.S2_ATTEMPTS
    s2_reset(monkeypatch, [429] * attempts * 2 + [200] + [429] * attempts * 2 + [200])
    for q in ["q1", "q2", "q3", "q4", "q5"]:
        search.semantic_scholar.search_semantic_scholar(q)
    assert search.semantic_scholar.search_semantic_scholar("q6")  # still searched: never 3 failures in a row
