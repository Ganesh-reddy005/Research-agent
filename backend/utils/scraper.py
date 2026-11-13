"""Full text of the top sources, for indexing. Publishers often refuse automated readers (403), so each
source is tried by several routes, the most open first, before falling back to its abstract:
  1. arXiv: an arXiv DOI or link is read from arxiv.org, which doesn't block readers
  2. an open-access PDF the search provider returned (Semantic Scholar, OpenAlex)
  3. the source's own link
  4. Unpaywall: a legal open-access copy found by DOI (only when CONTACT_EMAIL is set)
  5. Tavily Extract, for whatever is still unread: one call, using Tavily credits
Pages are read through Jina Reader, which turns HTML and PDFs into text."""
import asyncio
import json
import os
import re
import urllib.error
import urllib.request
import requests

JINA = "https://r.jina.ai/"
UNPAYWALL = "https://api.unpaywall.org/v2/"
MIN_TEXT = 3000  # shorter "full text" is a block, landing or abstract page (papers run 20k+ characters)
_DOI = re.compile(r"(10\.\d{4,9}/[^\s?#]+)")
_ARXIV_DOI = re.compile(r"10\.48550/arxiv\.([\w.\-/]+)", re.IGNORECASE)
_ARXIV_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/([\w.\-/]+?)(?:\.pdf)?$")


def doi_of(url: str) -> str | None:
    match = _DOI.search(url or "")
    return match.group(1).rstrip(".") if match else None


def arxiv_link(url: str) -> str | None:
    """The full paper on arxiv.org (its PDF; the abs page holds only the abstract) for an arXiv DOI or link."""
    match = _ARXIV_DOI.search(url or "") or _ARXIV_URL.search(url or "")
    return f"https://arxiv.org/pdf/{match.group(1)}" if match else None


def candidates(source: dict) -> list[str]:
    """The links to try for one source, most open first, without repeats."""
    url = source.get("url") or ""
    links = [arxiv_link(url), source.get("pdf_url"), url]
    return list(dict.fromkeys(link for link in links if link and link.startswith("http")))


def _jina(url: str, timeout: int) -> str:
    request = urllib.request.Request(JINA + url, headers={"Accept": "application/json", "User-Agent": "ResearchAgent/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = json.loads(response.read().decode("utf-8")).get("data", {}).get("content", "") or ""
            return text if len(text) >= MIN_TEXT else ""
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return ""


def unpaywall_link(doi: str) -> str | None:
    """A legal open-access copy of a DOI, if one exists (Unpaywall asks for a contact email)."""
    email = os.getenv("CONTACT_EMAIL")
    if not doi or not email:
        return None
    try:
        data = requests.get(UNPAYWALL + doi, params={"email": email}, timeout=10).json()
    except (requests.RequestException, ValueError):
        return None
    best = data.get("best_oa_location") or {}
    return best.get("url_for_pdf") or best.get("url")


def read_source(source: dict, timeout: int = 15) -> tuple[str, str]:
    """(text, how it was read) for one source, or ("", "") if no open route worked."""
    for link in candidates(source):
        text = _jina(link, timeout)
        if text:
            route = "arXiv" if "arxiv.org" in link else "open-access PDF" if link == source.get("pdf_url") else "page"
            return text, route
    copy = unpaywall_link(doi_of(source.get("url") or ""))
    if copy and copy not in candidates(source):
        text = _jina(copy, timeout)
        if text:
            return text, "Unpaywall"
    return "", ""


def tavily_extract(urls: list[str]) -> dict[str, str]:
    """{url: text} from Tavily Extract, which reads pages through its own servers; one call for all."""
    key = os.getenv("TAVILY_API_KEY")
    if not urls or not key:
        return {}
    try:
        from tavily import TavilyClient
        data = TavilyClient(api_key=key).extract(urls=urls[:20], format="markdown")
    except Exception as e:
        print(f"[Scraper] Tavily Extract failed: {e}")
        return {}
    return {r.get("url"): r.get("raw_content") or "" for r in data.get("results", []) if len(r.get("raw_content") or "") >= MIN_TEXT}


async def process_sources_with_full_text(sources: list, max_sources: int = 15) -> list:
    """The top sources with `full_text` (and `read_via`): the paper itself where any route can read it,
    otherwise its abstract."""
    top = sources[:max_sources]
    results = await asyncio.gather(*(asyncio.to_thread(read_source, s) for s in top))
    unread = [s for s, (text, _) in zip(top, results) if not text]
    extracted = await asyncio.to_thread(tavily_extract, [s["url"] for s in unread if s.get("url")])
    routes = {}
    for source, (text, route) in zip(top, results):
        if not text and extracted.get(source.get("url")):
            text, route = extracted[source["url"]], "Tavily"
        source["full_text"] = text or source.get("summary", "")
        source["read_via"] = route or "abstract"
        routes[source["read_via"]] = routes.get(source["read_via"], 0) + 1
    print("[Scraper] Read: " + ", ".join(f"{n} via {route}" for route, n in sorted(routes.items(), key=lambda r: -r[1])))
    return top
