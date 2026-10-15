import asyncio
from utils.events import report_progress
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.vectorstore import qdrant_configured, research_collection, ensure_collection, get_vector_store
from utils.scraper import process_sources_with_full_text

async def indexer_node(state):
    print("--- INDEXER AGENT ---")
    sources = state.get("raw_sources", [])
    topic = state.get("topic")
    
    if not sources:
        return {"current_step": "indexer"}
        
    if not qdrant_configured():
        print("QDRANT_URL not found. Skipping indexing.")
        return {"current_step": "indexer"}
        
    thread_id = state.get("thread_id", "default_thread")
    if not thread_id and getattr(state, "configurable", None):
        thread_id = state.configurable.get("thread_id", "default_thread")
        
    collection_name = research_collection(thread_id)
    
    # Create collection sized for the configured embedding model
    await asyncio.to_thread(ensure_collection, collection_name)
    
    print(f"Scraping deep full-text for top 15 sources...")
    await report_progress(f"Reading the top {min(15, len(sources))} sources in full")
    deep_sources = await process_sources_with_full_text(sources, max_sources=15)
    
    # Prepare chunker
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    # Splitting into chunks
    docs = []
    print("Chunking source texts...")
    for src in deep_sources:
        text = f"Title: {src.get('title')}\nSource: {src.get('source')}\n\n{src.get('full_text', src.get('summary', ''))}"
        
        chunks = text_splitter.split_text(text)
        for chunk in chunks:
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "topic": topic,
                    "url": src.get("url"),
                    "title": src.get("title"),
                    "source": src.get("source"),
                    "thread_id": thread_id
                }
            ))
            
    # Sources beyond the ones read in full: index their abstract/snippet so they stay searchable
    for src in sources[len(deep_sources):]:
        if src.get("summary"):
            docs.append(Document(
                page_content=f"Title: {src.get('title')}\nSource: {src.get('source')}\n\n{src['summary']}",
                metadata={"topic": topic, "url": src.get("url"), "title": src.get("title"),
                          "source": src.get("source"), "thread_id": thread_id}
            ))

    print(f"Created {len(docs)} text chunks. Indexing into Qdrant...")
    await report_progress(f"Indexing {len(docs)} passages for retrieval")
        
    # Store in Qdrant
    await get_vector_store(collection_name).aadd_documents(docs)
    
    return {"current_step": "indexer", "indexed_count": len(docs)}
