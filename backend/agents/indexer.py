import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.llm import OpenRouterEmbeddings
from utils.scraper import process_sources_with_full_text

async def indexer_node(state):
    print("--- INDEXER AGENT ---")
    sources = state.get("raw_sources", [])
    topic = state.get("topic")
    
    if not sources:
        return {"current_step": "indexer"}
        
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        print("QDRANT_URL not found. Skipping indexing.")
        return {"current_step": "indexer"}
        
    # Initialize embeddings
    embeddings = OpenRouterEmbeddings()
    
    # Initialize Qdrant client
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    thread_id = state.get("thread_id", "default_thread")
    if not thread_id and getattr(state, "configurable", None):
        thread_id = state.configurable.get("thread_id", "default_thread")
        
    collection_name = f"research_{thread_id.replace('-', '_')}"
    
    # Create collection if it doesn't exist
    # 1024 is the dimensionality for mistralai/mistral-embed-2312
    try:
        client.get_collection(collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)
        )
    
    print(f"Scraping deep full-text for top 15 sources...")
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
            
    print(f"Created {len(docs)} text chunks. Indexing into Qdrant...")
        
    # Store in Qdrant
    QdrantVectorStore.from_documents(
        docs,
        embeddings,
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name
    )
    
    return {"current_step": "indexer", "indexed_count": len(docs)}
