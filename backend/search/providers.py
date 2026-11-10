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

_ARXIV_STOPWORDS = {"a", "an", "and", "or", "the", "of", "for", "in", "on", "with", "to", "via", "using", "latest", "recent", "new", "papers"}

def _arxiv_all_terms(query):
    """'sparse attention for long-context LLMs 2026' -> all:sparse AND all:attention AND all:long AND ...
    arXiv ORs bare words, which is noise once results are sorted by date instead of relevance."""
    words = [re.sub(r"[^\w]", "", w) for w in re.split(r"[\s\-]+", query)]
    terms = [w for w in words if w and w.lower() not in _ARXIV_STOPWORDS and not re.fullmatch(r"(19|20)\d\d", w)]
    return " AND ".join(f"all:{t}" for t in terms)

def search_arxiv(query, max_results=3, newest_first=False):
    if newest_first:
        terms = _arxiv_all_terms(query)
        if terms:
            url = (f'https://export.arxiv.org/api/query?search_query={urllib.parse.quote(terms, safe=":")}'
                   f'&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending')
            found = _fetch_arxiv(url, query)
            if found:
                return found
        # Nothing matched every term: fall back to relevance ranking
    url = f'https://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}'
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
        return [search_openalex, search_arxiv, search_core]
    if kind == "web":
        return [search_web]
    return []
