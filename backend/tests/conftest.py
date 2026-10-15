import os
import sys

# Pin every external-service variable BEFORE any app module runs load_dotenv(),
# which never overrides variables that are already set. Tests must not touch
# real keys, Qdrant, Supabase or Postgres.
TEST_ENV = {
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "GROQ_API_KEY": "test-groq-key",
    "TAVILY_API_KEY": "",
    "CORE_API_KEY": "",
    "OPENALEX_API_KEY": "",
    "QDRANT_URL": "",
    "QDRANT_API_KEY": "",
    "SUPABASE_URL": "",
    "SUPABASE_SERVICE_ROLE_KEY": "",
    "DATABASE_URL": "",
}
os.environ.update(TEST_ENV)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
