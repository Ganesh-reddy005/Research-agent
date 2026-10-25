"""Work out what a repository's project is, from its README, manifests, file tree and key files.

The result, a project profile, is what every later agent reads about the project."""
import json
import re
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from repo.github import FetchedRepo
from repo.scanner import RepoSnapshot, key_files
from utils.llm import ainvoke_llm

SYSTEM_PROMPT = """You are a senior engineer and research supervisor reading a student's or researcher's code repository
so that a research paper can be written about the project.

Describe ONLY what the repository shows. Never invent results, metrics, datasets or features.
If something is not in the repository, say "Not found in the repository".
Be concise: at most 2 sentences per text field, at most 6 architecture components and 8 items per list.

Return STRICTLY this JSON object:
{
  "title": "A specific, academic paper title for this project",
  "summary": "2-3 sentences: what the project is and does",
  "problem": "The problem or need the project addresses",
  "approach": "How it solves it: the method, model or system design",
  "architecture": [{"component": "Name", "role": "What it does", "files": ["path/in/repo.py"]}],
  "tech_stack": ["Language, framework or library"],
  "key_algorithms": ["Algorithm, model or technique the code implements"],
  "data": ["Datasets, data sources or inputs the code uses"],
  "evaluation": "Tests, benchmarks, metrics or results present in the repository, or 'Not found in the repository'",
  "limitations": ["Gaps or limitations visible in the code"],
  "related_work_queries": ["5 academic search queries for related work on this project's problem and techniques"]
}"""


def _prompt(fetched: FetchedRepo, snapshot: RepoSnapshot, notes: str) -> str:
    manifests = "\n\n".join(f"--- {path}\n{text[:2000]}" for path, text in snapshot.manifests.items())
    files = "\n\n".join(f"--- {path}\n{excerpt}" for path, excerpt in key_files(snapshot))
    languages = ", ".join(f"{lang} ({lines} lines)" for lang, lines in snapshot.languages.items())
    return f"""Repository: {fetched.repo.full_name} (branch {fetched.branch})
GitHub description: {fetched.description or 'none'}
Topics: {', '.join(fetched.topics) or 'none'}
Languages: {languages or 'unknown'}
Author's notes about the project: {notes or 'none'}

README:
{snapshot.readme[:8000] or 'No README.'}

File tree:
{snapshot.tree}

Dependency and build files:
{manifests or 'none'}

Key source files (excerpts):
{files or 'none'}"""


def _parse(content: str) -> dict:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _fallback(fetched: FetchedRepo) -> dict:
    """Enough to carry on when the analysis can't be parsed: the user still reviews it."""
    return {
        "title": fetched.repo.name.replace("-", " ").replace("_", " ").title(),
        "summary": fetched.description or f"The {fetched.repo.full_name} repository.",
        "related_work_queries": [fetched.repo.name.replace("-", " ")] + fetched.topics[:4],
    }


async def profile_repo(fetched: FetchedRepo, snapshot: RepoSnapshot, notes: str = "") -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=_prompt(fetched, snapshot, notes))]
    response = await ainvoke_llm(messages, agent_name="repo_analysis", max_tokens=8000)
    profile = _parse(response.content) or _fallback(fetched)
    # Facts about the repository come from GitHub, not the model
    return {
        **profile,
        "name": fetched.repo.full_name,
        "url": fetched.repo.url,
        "branch": fetched.branch,
        "commit": fetched.commit,
        "license": fetched.license,
        "stats": {
            "files": len(snapshot.files),
            "lines": snapshot.total_lines,
            "languages": snapshot.languages,
        },
        "analysed_on": date.today().isoformat(),
    }
