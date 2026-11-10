"""Where Lume searches: each provider takes a query and returns sources as
{"title", "url", "summary", "source", "year"?, "authors"?}. Providers are blocking (HTTP clients);
callers run them in worker threads. Searches are grouped by the kind of need they serve."""
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import requests
from tavily import TavilyClient
from utils.vectorstore import qdrant_configured, library_collection, collection_exists, get_vector_store
from search.semantic_scholar import search_semantic_scholar

def search_private_library(query, user_id, max_results=5):
    sources = []
    if not qdrant_configured() or not user_id:
        return sources
        
    collection_name = library_collection(user_id)
    
    try:
        if not collection_exists(collection_name):
            return sources

        docs = get_vector_store(collection_name).similarity_search(query, k=max_results)
        for d in docs:
            sources.append({
                "title": d.metadata.get("source", "Private Document"),
                "url": f"local://{d.metadata.get('source')}",
                "summary": d.page_content[:500] + "...",
                "source": "Private Library"
            })
    except Exception as e:
        print(f"Private library search failed: {e}")
    return sources

def search_core(query, max_results=3):
    sources = []
    api_key = os.getenv("CORE_API_KEY")
    if not api_key:
        return sources
    
    try:
        url = f"https://api.core.ac.uk/v3/search/works"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"q": query, "limit": max_results}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for work in data.get("results", []):
                title = work.get("title", "No Title")
                # sourceFulltextUrls can be an empty list
                url = work.get("downloadUrl") or (work.get("sourceFulltextUrls") or [None])[0] or "https://core.ac.uk/"
                summary = work.get("abstract") or "Detailed academic paper from CORE."
                sources.append({"title": title, "url": url, "summary": summary, "source": "CORE"})
    except Exception as e:
        print(f"CORE search failed for '{query}': {e}")
    return sources

def _openalex_abstract(inverted_index):
    """OpenAlex ships abstracts as {word: [positions]}; rebuild the text."""
    if not inverted_index:
        return ""
    positions = [(pos, word) for word, places in inverted_index.items() for pos in places]
    return " ".join(word for _, word in sorted(positions))

def search_openalex(query, max_results=3):
    sources = []
    api_key = os.getenv("OPENALEX_API_KEY")
    try:
        email = os.getenv("CONTACT_EMAIL", "research-agent@example.com")
        headers = {"User-Agent": f"mailto:{email}"}
        if api_key:
            headers["api-key"] = api_key
            
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page={max_results}"
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for work in data.get("results", []):
                title = work.get("title") or "No Title"
                url = work.get("doi") or work.get("id")
                summary = _openalex_abstract(work.get("abstract_inverted_index")) or "No abstract available."
                authors = [a.get("author", {}).get("display_name") for a in work.get("authorships", [])]
                sources.append({"title": title, "url": url, "summary": summary, "source": "OpenAlex",
                                "year": work.get("publication_year"), "authors": [a for a in authors if a][:6]})
    except Exception as e:
        print(f"OpenAlex search failed: {e}")
    return sources

# Words arXiv's index ignores: requiring one ("all:Is") matches nothing, so they're left out of AND queries
_ARXIV_STOPWORDS = {
    "a", "an", "and", "or", "the", "of", "for", "in", "on", "with", "to", "via", "using", "latest", "recent", "new",
    "papers", "is", "are", "was", "were", "be", "been", "all", "any", "you", "your", "we", "our", "it", "its", "this",
    "that", "these", "those", "how", "what", "when", "which", "who", "why", "can", "do", "does", "from", "by", "as",
    "at", "into", "than", "then", "there", "their", "not", "no", "but", "if", "so", "about",
}

ARXIV_LEADING_TERMS = 4  # queries lead with names and title words, so these carry the meaning

def _arxiv_all_terms(query, limit=None):
    """'sparse attention for long-context LLMs 2026' -> all:sparse AND all:attention AND all:long AND ...
    arXiv ORs bare words, so "Attention Is All You Need" would match every paper mentioning attention.
    limit keeps only the leading terms."""
    words = [re.sub(r"[^\w]", "", w) for w in re.split(r"[\s\-]+", query)]
    terms = [w for w in words if w and w.lower() not in _ARXIV_STOPWORDS and not re.fullmatch(r"(19|20)\d\d", w)]
    return " AND ".join(f"all:{t}" for t in terms[:limit])

ARXIV_API = "https://export.arxiv.org/api/query"

def search_arxiv(query, max_results=3, newest_first=False):
    """Papers matching every keyword, by relevance (or newest first). If none match them all, papers
    matching the leading keywords; failing that, any-word relevance ranking."""
    order = "&sortBy=submittedDate&sortOrder=descending" if newest_first else "&sortBy=relevance"
    attempts = dict.fromkeys(filter(None, [_arxiv_all_terms(query), _arxiv_all_terms(query, ARXIV_LEADING_TERMS)]))
    for terms in attempts:  # de-duplicated: a short query is tried once
        url = f"{ARXIV_API}?search_query={urllib.parse.quote(terms, safe=':')}&start=0&max_results={max_results}{order}"
        found = _fetch_arxiv(url, query)
        if found:
            return found
    url = f"{ARXIV_API}?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}&sortBy=relevance"
    return _fetch_arxiv(url, query)

def _fetch_arxiv(url, query):
    sources = []
    try:
        response = urllib.request.urlopen(url, timeout=8)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
            link = entry.find('atom:id', namespace).text
            published = entry.find('atom:published', namespace)
            year = int(published.text[:4]) if published is not None and published.text else None
            authors = [a.findtext('atom:name', default='', namespaces=namespace) for a in entry.findall('atom:author', namespace)]
            sources.append({"title": title, "url": link, "summary": summary, "source": "arXiv", "year": year,
                            "authors": [a for a in authors if a][:6]})
    except Exception as e:
        print(f"arXiv skipped for '{query}': {e}")
    return sources

def search_web(query, max_results=5):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    res = TavilyClient(api_key=key).search(query=query, search_depth="basic", max_results=max_results)
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "summary": r.get("content", ""), "source": "Web"}
            for r in res.get("results", [])]

def searchers(kind):
    """The providers for a kind of need. Looked up at call time, so tests can replace a provider."""
    if kind == "papers":
        return [search_semantic_scholar, search_openalex, search_arxiv, search_core]
    if kind == "web":
        return [search_web]
    return []
