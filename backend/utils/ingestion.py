import asyncio
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.vectorstore import library_collection, ensure_collection, get_vector_store

def _ingest_pdf(file_path: str, user_id: str, filename: str) -> str:
    # 1. Read PDF
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"

    if not text.strip():
        raise ValueError("Could not extract text from PDF")

    # 2. Chunk text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    chunks = text_splitter.split_text(text)

    # 3. User-specific collection for their private library
    collection_name = library_collection(user_id)
    ensure_collection(collection_name)

    # 4. Store in Qdrant with metadata
    metadatas = [{"source": filename, "user_id": str(user_id)} for _ in chunks]
    get_vector_store(collection_name).add_texts(texts=chunks, metadatas=metadatas)

    return collection_name

async def process_pdf_ingestion(file_path: str, user_id: str, filename: str):
    """
    Parses a PDF, chunks it, embeds it, and stores it in the user's Qdrant collection.
    Runs in a worker thread: parsing and embedding are slow and fully synchronous.
    """
    return await asyncio.to_thread(_ingest_pdf, file_path, user_id, filename)
