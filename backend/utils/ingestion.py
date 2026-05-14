import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from utils.llm import OpenRouterEmbeddings

async def process_pdf_ingestion(file_path: str, user_id: str, filename: str):
    """
    Parses a PDF, chunks it, embeds it, and stores it in the user's Qdrant collection.
    """
    # 1. Read PDF
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    if not text.strip():
        raise ValueError("Could not extract text from PDF")

    # 2. Chunk text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    chunks = text_splitter.split_text(text)

    # 3. Setup Qdrant
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    embeddings = OpenRouterEmbeddings()
    
    # User-specific collection for their private library
    collection_name = f"user_{str(user_id).replace('-', '_')}_library"
    
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    # Ensure collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE), # Assuming 1024 for Mistral/OpenRouter
        )

    # 4. Store in Qdrant
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    
    # Add metadata
    metadatas = [{"source": filename, "user_id": str(user_id)} for _ in chunks]
    vector_store.add_texts(texts=chunks, metadatas=metadatas)
    
    return collection_name
