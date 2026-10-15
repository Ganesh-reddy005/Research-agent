import os
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from graph.workflow import build_graph
from graph.brainstorm import build_brainstorm_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver

from api.routers import research, library, sessions, brainstorm, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
            await checkpointer.setup()
            app.state.graph = build_graph(checkpointer=checkpointer)
            app.state.brainstorm_graph = build_brainstorm_graph(checkpointer=checkpointer)
            yield
    else:
        print("WARNING: DATABASE_URL not found, falling back to MemorySaver")
        checkpointer = MemorySaver()
        app.state.graph = build_graph(checkpointer=checkpointer)
        app.state.brainstorm_graph = build_brainstorm_graph(checkpointer=checkpointer)
        yield

app = FastAPI(title="AI Research Production System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(research.router)
app.include_router(library.router)
app.include_router(sessions.router)
app.include_router(brainstorm.router)
app.include_router(chat.router)

@app.get("/")
def home():
    return {"message": "AI Research Production System"}
