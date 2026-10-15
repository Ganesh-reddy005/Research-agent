import os
import asyncio
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import requests
import json
from tavily import TavilyClient
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
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
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for work in data.get("results", []):
                title = work.get("title", "No Title")
                url = work.get("downloadUrl") or work.get("sourceFulltextUrls", [None])[0] or "https://core.ac.uk/"
                summary = work.get("abstract") or "Detailed academic paper from CORE."
                sources.append({"title": title, "url": url, "summary": summary, "source": "CORE"})
    except Exception as e:
        print(f"CORE search failed for '{query}': {e}")
    return sources

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
                title = work.get("title", "No Title")
                url = work.get("doi") or work.get("id")
                summary = "Detailed academic paper."
                sources.append({"title": title, "url": url, "summary": summary, "source": "OpenAlex"})
    except Exception as e:
        print(f"OpenAlex search failed: {e}")
    return sources

def search_arxiv(query, max_results=3):
    url = f'http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}'
    sources = []
    try:
        # Reduced timeout to 3s for maximum responsiveness
        response = urllib.request.urlopen(url, timeout=3)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
            link = entry.find('atom:id', namespace).text
            sources.append({"title": title, "url": link, "summary": summary, "source": "arXiv"})
    except Exception as e:
        print(f"arXiv skipped for '{query}': {e}")
    return sources

async def retriever_node(state):
    print("--- RETRIEVER AGENT ---")
    topic = state.get("topic")
    plan = state.get("research_plan", {})
    mode = state.get("research_mode", "deep")
    
    num_queries = 3 if mode == "light" else 7
    results_per_query = 3 if mode == "light" else 5
    
    sections = plan.get("sections", [])
    section_texts = [f"{s.get('title')}: {s.get('description')}" for s in sections]
    
    system_prompt = f"Generate exactly {num_queries} distinct, highly technical search queries. Return strictly as a JSON array of strings."
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=f"Topic: {topic}\nPlan Sections:\n" + "\n".join(section_texts))]
    
    response = await ainvoke_llm(messages, agent_name="retrieval")
    try:
        content = response.content.strip()
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        search_queries = json.loads(content)
    except:
        search_queries = [topic]

    tavily_key = os.getenv("TAVILY_API_KEY")
    tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
    
    all_sources = []
    normalized_queries = [str(q.get("query", q)) if isinstance(q, dict) else str(q) for q in search_queries]

    # PARALLEL SEARCH: every (query, source) pair runs in a worker thread so the
    # blocking HTTP clients never stall the event loop (and other users' streams).
    # gather() keeps submission order, so raw_sources order is deterministic.
    user_id = state.get("user_id")
    tasks = []
    for q in normalized_queries:
        # 1. Tavily
        if tavily:
            tasks.append(asyncio.to_thread(tavily.search, query=q, search_depth="basic", max_results=results_per_query))
        # 2. OpenAlex
        tasks.append(asyncio.to_thread(search_openalex, q, max_results=results_per_query))
        # 3. arXiv
        tasks.append(asyncio.to_thread(search_arxiv, q, max_results=results_per_query))
        # 4. CORE
        tasks.append(asyncio.to_thread(search_core, q, max_results=results_per_query))
        # 5. Private Library
        if user_id:
            tasks.append(asyncio.to_thread(search_private_library, q, user_id, max_results=results_per_query))

    for res in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(res, Exception):
            print(f"Search task failed: {res}")
        elif isinstance(res, dict) and "results" in res: # Tavily response
            web_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "summary": r.get("content", ""), "source": "Web"} for r in res.get("results", [])]
            all_sources.extend(web_results)
        elif isinstance(res, list): # OpenAlex, arXiv, CORE or private library result list
            all_sources.extend(res)
        
    seen_urls = set()
    unique_sources = []
    for source in all_sources:
        url = source.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(source)
            
    return {"raw_sources": unique_sources, "current_step": "retriever"}
