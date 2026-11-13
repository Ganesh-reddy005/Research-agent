"""Semantic Scholar as a paper provider: relevance-ranked search with citation counts.

Its API allows 1 request a second, so calls are queued through one throttle. It also refuses some
requests (429) even at that pace, so each call retries a few times; only when several calls in a row
fail outright is it skipped for a while, instead of slowing every search down."""
import os
import time
import threading
import requests

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = "title,abstract,year,authors,url,externalIds,citationCount,venue,openAccessPdf"
S2_INTERVAL = 1.1  # seconds between calls: Semantic Scholar allows about 1 request a second, key or not
S2_ATTEMPTS = 4  # tries per search: refusals are intermittent, so a retry usually gets through
S2_BACKOFF = 1.0  # extra seconds before each retry, on top of the throttle
S2_FAILS_BEFORE_SKIP = 3  # searches in a row that fail every attempt before Semantic Scholar is skipped
S2_COOL_OFF = 600  # seconds to skip Semantic Scholar after that
_s2_lock = threading.Lock()
_s2_last_call = 0.0
_s2_skip_until = 0.0
_s2_failed_calls = 0

def _s2_get(params):
    """One throttled search; searches run in parallel threads, so they queue here. Retries on 429;
    after S2_FAILS_BEFORE_SKIP searches in a row fail every attempt, skips Semantic Scholar for S2_COOL_OFF."""
    global _s2_last_call, _s2_skip_until, _s2_failed_calls
    headers = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}
    for attempt in range(S2_ATTEMPTS):
        if attempt:
            time.sleep(S2_BACKOFF)
        with _s2_lock:
            time.sleep(max(0.0, _s2_last_call + S2_INTERVAL - time.monotonic()))
            _s2_last_call = time.monotonic()
        response = requests.get(S2_SEARCH, params=params, headers=headers, timeout=10)
        if response.status_code != 429:
            _s2_failed_calls = 0
            return response
    _s2_failed_calls += 1
    if _s2_failed_calls >= S2_FAILS_BEFORE_SKIP:
        _s2_skip_until, _s2_failed_calls = time.monotonic() + S2_COOL_OFF, 0
        print(f"Semantic Scholar keeps rate limiting; skipping it for {S2_COOL_OFF // 60} minutes.")
    return response

def s2_source(paper):
    """A Semantic Scholar paper as a source. The URL is the most readable copy: arXiv, then DOI, then S2."""
    ids = paper.get("externalIds") or {}
    url = (f"https://arxiv.org/abs/{ids['ArXiv']}" if ids.get("ArXiv")
           else f"https://doi.org/{ids['DOI']}" if ids.get("DOI") else paper.get("url"))
    authors = [a.get("name") for a in paper.get("authors") or [] if a.get("name")]
    return {"title": paper.get("title") or "No Title", "url": url, "summary": paper.get("abstract") or "No abstract available.",
            "source": "Semantic Scholar", "year": paper.get("year"), "authors": authors[:6],
            "citations": paper.get("citationCount"),
            "pdf_url": (paper.get("openAccessPdf") or {}).get("url") or None}  # an open copy, for reading in full

def search_semantic_scholar(query, max_results=3):
    """Relevance-ranked search over 200M+ papers, with citation counts, so well-known work surfaces first."""
    if time.monotonic() < _s2_skip_until:
        return []
    try:
        response = _s2_get({"query": query, "limit": max_results, "fields": S2_FIELDS})
        if response.status_code == 200:
            return [s2_source(p) for p in response.json().get("data") or [] if p.get("title")]
        print(f"Semantic Scholar returned {response.status_code} for '{query}'")
    except Exception as e:
        print(f"Semantic Scholar search failed for '{query}': {e}")
    return []
