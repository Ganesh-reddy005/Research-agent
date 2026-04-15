import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from tavily import TavilyClient
import concurrent.futures

def search_arxiv(query, max_results=2):
    url = f'http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}'
    sources = []
    try:
        response = urllib.request.urlopen(url)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
            link = entry.find('atom:id', namespace).text
            sources.append({"title": title, "url": link, "summary": summary})
    except Exception as e:
        print(f"arXiv search failed: {e}")
    return sources

def search_single_query(topic, tavily):
    results = []
    # 1. Tavily Search
    if tavily:
        try:
            response = tavily.search(query=topic, search_depth="basic", max_results=2)
            for res in response.get("results", []):
                results.append({
                    "title": res.get("title", ""),
                    "url": res.get("url", ""),
                    "summary": res.get("content", "")
                })
        except Exception as e:
            print(f"Tavily search failed for topic '{topic}': {e}")
            
    # 2. arXiv
    arxiv_results = search_arxiv(topic, max_results=2)
    results.extend(arxiv_results)
    return results

def retriever_node(state):
    print("--- RETRIEVER AGENT ---")
    search_queries = state.get("search_queries", [])
    if not search_queries:
        search_queries = [state.get("query")]
        
    tavily_key = os.getenv("TAVILY_API_KEY")
    tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
    
    all_sources = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_single_query, q, tavily) for q in search_queries]
        for future in concurrent.futures.as_completed(futures):
            all_sources.extend(future.result())
        
    seen_urls = set()
    unique_sources = []
    for source in all_sources:
        if source.get("url") not in seen_urls:
            seen_urls.add(source["url"])
            unique_sources.append(source)
            
    # Limit to top 15 sources to avoid overwhelming context
    return {"sources": unique_sources[:15]}
