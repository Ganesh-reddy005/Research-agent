import asyncio
from fastapi import APIRouter, Depends, Request, Response
from utils.auth import get_current_user, get_supabase_client, verify_session
from utils.vectorstore import qdrant_configured, get_qdrant_client, research_collection, repo_collection

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.get("")
async def list_sessions(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    res = await asyncio.to_thread(supabase.table("sessions").select("*").eq("user_id", user.id).order("created_at", desc=True).execute)
    return res.data

def _delete_collections(thread_id: str) -> None:
    """The session's indexed sources and repository code (absent for brainstorms)."""
    client = get_qdrant_client()
    for name in (research_collection(thread_id), repo_collection(thread_id)):
        if client.collection_exists(name):
            client.delete_collection(name)

def _delete_experiment(thread_id: str) -> None:
    """The coding agent's workspace on disk and the task's Docker image, if the session had experiments."""
    import shutil
    from experiments.workspace import WORKSPACES
    shutil.rmtree(WORKSPACES / thread_id, ignore_errors=True)
    try:
        import docker
        docker.from_env().images.remove(f"lume-task:{thread_id[:12]}", force=True)
    except Exception:
        pass  # no image, or Docker isn't running

@router.delete("/{thread_id}", status_code=204)
async def delete_session(thread_id: str, req: Request, user=Depends(get_current_user)):
    """Delete a research project or brainstorm and everything stored for it.
    The History row goes last, so a failed cleanup can be retried."""
    await verify_session(thread_id, user.id)
    await req.app.state.checkpointer.adelete_thread(thread_id)
    if qdrant_configured():
        try:
            await asyncio.to_thread(_delete_collections, thread_id)
        except Exception as e:  # orphaned vectors are harmless; don't block the delete
            print(f"Could not delete Qdrant collections of {thread_id}: {e}")
    await asyncio.to_thread(_delete_experiment, thread_id)
    supabase = get_supabase_client()
    await asyncio.to_thread(supabase.table("sessions").delete().eq("thread_id", thread_id).eq("user_id", user.id).execute)
    return Response(status_code=204)
