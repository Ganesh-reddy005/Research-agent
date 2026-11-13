import os
import asyncio
from functools import lru_cache
import httpx
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from utils.llm import OpenRouterEmbeddings

def qdrant_configured() -> bool:
    return bool(os.getenv("QDRANT_URL"))

@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    # 30 s: writes of a few hundred vectors can take longer than the client's default over a slow link
    return QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"), timeout=30)

BATCH = 32
ATTEMPTS = 3
TRANSIENT = (ResponseHandlingException, httpx.TransportError, ConnectionError, TimeoutError)


async def add_documents_reliably(store, docs, batch: int = BATCH) -> int:
    """Index docs in small batches, retrying each on network drops (resets, timeouts), so one dropped
    connection doesn't lose the whole run. Returns how many were indexed."""
    for start in range(0, len(docs), batch):
        for attempt in range(ATTEMPTS):
            try:
                await store.aadd_documents(docs[start:start + batch])
                break
            except TRANSIENT as e:
                if attempt == ATTEMPTS - 1:
                    raise
                print(f"Qdrant write failed ({e}); retrying batch {start // batch + 1}")
                await asyncio.sleep(2 * (attempt + 1))
    return len(docs)

@lru_cache(maxsize=1)
def get_embeddings() -> OpenRouterEmbeddings:
    return OpenRouterEmbeddings()

@lru_cache(maxsize=1)
def embedding_dim() -> int:
    """Vector size of EMBEDDING_MODEL, probed once instead of hard-coded."""
    return len(get_embeddings().embed_query("dimension probe"))

def research_collection(thread_id: str) -> str:
    return f"research_{thread_id.replace('-', '_')}"

def repo_collection(thread_id: str) -> str:
    """Code of the project a research session writes about (kept apart from the literature)."""
    return f"repo_{thread_id.replace('-', '_')}"

def library_collection(user_id) -> str:
    return f"user_{str(user_id).replace('-', '_')}_library"

def collection_exists(name: str) -> bool:
    return get_qdrant_client().collection_exists(name)

def ensure_collection(name: str) -> None:
    """Create the collection sized for the current embedding model, or fail loudly
    if it already exists with a different size (i.e. EMBEDDING_MODEL was changed)."""
    client = get_qdrant_client()
    dim = embedding_dim()
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
        return
    existing = client.get_collection(name).config.params.vectors.size
    if existing != dim:
        raise ValueError(
            f"Qdrant collection '{name}' has vector size {existing}, but EMBEDDING_MODEL "
            f"produces {dim}. Delete the collection or switch back to the original model."
        )

def get_vector_store(name: str) -> QdrantVectorStore:
    return QdrantVectorStore(client=get_qdrant_client(), collection_name=name, embedding=get_embeddings())
