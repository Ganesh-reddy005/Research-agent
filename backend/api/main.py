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
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from api.routers import research, library, sessions, brainstorm, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # A pool instead of from_conn_string's single connection: Supabase drops idle
        # connections, and check= swaps a dead one for a fresh one before handing it out
        async with AsyncConnectionPool(
            db_url,
            min_size=1,
            max_size=10,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            check=AsyncConnectionPool.check_connection,
            max_idle=300,
            open=False,
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            app.state.checkpointer = checkpointer
            app.state.graph = build_graph(checkpointer=checkpointer)
            app.state.brainstorm_graph = build_brainstorm_graph(checkpointer=checkpointer)
            yield
    else:
        print("WARNING: DATABASE_URL not found, falling back to MemorySaver")
        checkpointer = MemorySaver()
        app.state.checkpointer = checkpointer
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
