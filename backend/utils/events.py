from langchain_core.callbacks import adispatch_custom_event

async def emit_event(name: str, data: dict):
    """Live UI event (progress, search start/end) for the current graph run.
    A no-op when nobody is streaming, e.g. a plain ainvoke or a direct node call."""
    try:
        await adispatch_custom_event(name, data)
    except RuntimeError:
        pass

async def report_progress(message: str):
    await emit_event("progress", {"message": message})
