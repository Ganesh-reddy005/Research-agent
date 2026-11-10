"""Semantic Scholar as a paper provider: relevance-ranked search with citation counts.

Its API allows about 1 request a second (with or without a key), so calls are queued through one
throttle; when it keeps refusing, it is skipped for a while instead of slowing every search down."""
import os
import time
import threading
import requests

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = "title,abstract,year,authors,url,externalIds,citationCount,venue,openAccessPdf"
S2_INTERVAL = 1.1  # seconds between calls: Semantic Scholar allows about 1 request a second, key or not
S2_COOL_OFF = 600  # seconds to skip Semantic Scholar after it keeps refusing (e.g. no key and a busy shared pool)
_s2_lock = threading.Lock()
_s2_last_call = 0.0
_s2_skip_until = 0.0

def _s2_get(params):
    """One throttled call; searches run in parallel threads, so they queue here. Retries once on 429,
    then skips Semantic Scholar for S2_COOL_OFF seconds so later searches don't wait on it."""
    global _s2_last_call, _s2_skip_until
    headers = {"x-api-key": os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}
    for attempt in range(2):
        with _s2_lock:
            time.sleep(max(0.0, _s2_last_call + S2_INTERVAL - time.monotonic()))
            _s2_last_call = time.monotonic()
        response = requests.get(S2_SEARCH, params=params, headers=headers, timeout=10)
        if response.status_code != 429:
            return response
        time.sleep(2 * (attempt + 1))
    _s2_skip_until = time.monotonic() + S2_COOL_OFF
    print(f"Semantic Scholar is rate limiting; skipping it for {S2_COOL_OFF // 60} minutes. "
          "A free key (SEMANTIC_SCHOLAR_API_KEY) gives a dedicated limit.")
    return response

def s2_source(paper):
    """A Semantic Scholar paper as a source. The URL is the most readable copy: arXiv, then DOI, then S2."""
    ids = paper.get("externalIds") or {}
    url = (f"https://arxiv.org/abs/{ids['ArXiv']}" if ids.get("ArXiv")
           else f"https://doi.org/{ids['DOI']}" if ids.get("DOI") else paper.get("url"))
    authors = [a.get("name") for a in paper.get("authors") or [] if a.get("name")]
    return {"title": paper.get("title") or "No Title", "url": url, "summary": paper.get("abstract") or "No abstract available.",
            "source": "Semantic Scholar", "year": paper.get("year"), "authors": authors[:6],
            "citations": paper.get("citationCount")}

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
