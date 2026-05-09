import asyncio
import json
import urllib.request
import urllib.error

async def fetch_full_text(url: str, timeout: int = 15) -> str:
    """
    Fetch the full markdown text of a URL using Jina Reader API.
    Returns empty string on failure.
    """
    if set(("arxiv.org", "wikipedia.org")).intersection(url):
        # Already good clean APIs, but Jina handles them fine.
        pass

    jina_url = f"https://r.jina.ai/{url}"
    
    def _fetch():
        req = urllib.request.Request(
            jina_url,
            headers={
                "Accept": "application/json",
                # Optionally add an API key here if getting rate limited
                "User-Agent": "ResearchAgent/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data.get('data', {}).get('content', '')
        except urllib.error.URLError as e:
            print(f"[Scraper] Error fetching {url}: {e}")
        except Exception as e:
            print(f"[Scraper] Unexpected error fetching {url}: {e}")
        return ""
        
    return await asyncio.to_thread(_fetch)

async def process_sources_with_full_text(sources: list, max_sources: int = 15) -> list:
    """
    Takes an array of source dictionaries, grabs the top `max_sources`, 
    and appends a `full_text` key to them by downloading the contents.
    Returns the updated sources.
    """
    top_sources = sources[:max_sources]
    
    # Run fetch tasks concurrently
    tasks = [fetch_full_text(src.get('url')) for src in top_sources]
    full_texts = await asyncio.gather(*tasks)
    
    for i, _ in enumerate(top_sources):
        # Fall back to the snippet/summary if Jina failed to extract
        if not full_texts[i]:
            top_sources[i]['full_text'] = top_sources[i].get('summary', '')
        else:
            top_sources[i]['full_text'] = full_texts[i]
            
    return top_sources
