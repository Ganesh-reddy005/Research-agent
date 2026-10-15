import os
import asyncio
import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from utils.auth import get_current_user, get_supabase_client
from utils.ingestion import process_pdf_ingestion

router = APIRouter(prefix="/api/library", tags=["library"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user=Depends(get_current_user)):
    # Never build paths from the client-supplied name ("../../x.pdf")
    filename = os.path.basename((file.filename or "").replace("\\", "/"))
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        collection_name = await process_pdf_ingestion(temp_path, user.id, filename)

        supabase = get_supabase_client()
        await asyncio.to_thread(supabase.table("library").insert({
            "user_id": user.id,
            "filename": filename,
            "storage_path": f"library/{user.id}/{filename}",
            "parsing_status": "completed",
            "qdrant_collection_name": collection_name
        }).execute)

        return {"status": "success", "filename": filename, "collection": collection_name}
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("")
async def list_library(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    res = await asyncio.to_thread(supabase.table("library").select("*").eq("user_id", user.id).execute)
    return res.data
