import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from utils.llm import OpenRouterEmbeddings

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
    
    collection_name = "research_assistant"
    
    # Create collection if it doesn't exist
    # 1024 is the dimensionality for llama-nemotron-embed
    try:
        client.get_collection(collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)
        )
    
    # Prepare documents for LangChain Qdrant
    docs = []
    for src in sources:
        content = f"Title: {src.get('title')}\nSource: {src.get('source')}\nSummary: {src.get('summary')}\nURL: {src.get('url')}"
        docs.append(Document(
            page_content=content,
            metadata={
                "topic": topic,
                "url": src.get("url"),
                "title": src.get("title"),
                "source": src.get("source")
            }
        ))
        
    # Store in Qdrant
    QdrantVectorStore.from_documents(
        docs,
        embeddings,
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name
    )
    
    return {"current_step": "indexer", "indexed_count": len(docs)}
