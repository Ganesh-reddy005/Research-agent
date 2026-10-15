import asyncio
from fastapi import APIRouter, Depends
from utils.auth import get_current_user, get_supabase_client

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.get("")
async def list_sessions(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    res = await asyncio.to_thread(supabase.table("sessions").select("*").eq("user_id", user.id).order("created_at", desc=True).execute)
    return res.data
