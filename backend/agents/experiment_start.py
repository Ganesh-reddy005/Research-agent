"""Coding agent, where to start: look for existing open-source code that already does most of what the
brief needs (the user confirms the choice, since reading a large codebase costs tokens), or, when
nothing fits, design the experiment from scratch: evaluation first, then one variant per step."""
import asyncio
from agents.experiment_setup import spend
from experiments import lab as labs
from experiments.agent_runtime import run_phase
from experiments.prior_work import repositories_in_sources
from experiments.prompts import DESIGN, SCOUT
from experiments.toolbox import ToolContext
from experiments.workspace import WORKSPACES, Workspace
from utils.events import report_progress

IMPROVE, BUILD = "improve", "build"
SOURCES_SHOWN = 15


def _context(brief: dict) -> ToolContext:
    return ToolContext(code=None, target=brief.get("target", ""), goal=brief["metric"]["goal"])


async def scout_node(state):
    print("--- EXPERIMENT: FIND A STARTING POINT ---")
    brief = state["experiment_brief"]
    await report_progress("Looking for existing open-source code to start from")
    known = repositories_in_sources(state.get("raw_sources") or [])
    task = f"{labs.brief_text(brief)}\n\nRepositories the research already found:\n" + ("\n".join(known) or "none")
    result, usage = await run_phase("scout", "experiment_scout", SCOUT, task, _context(brief))
    chosen = result.get("starting_point") if isinstance(result.get("starting_point"), dict) else {}
    url = labs.clone_source(str(chosen.get("url", ""))) or ""
    alternatives = [{"url": str(a.get("url")), "why": str(a.get("why", ""))}
                    for a in result.get("alternatives") or [] if isinstance(a, dict) and labs.clone_source(str(a.get("url", "")))]
    start = {"url": url, "why": str(chosen.get("why", "")), "alternatives": alternatives[:4],
             "if_none": str(result.get("if_none", "")) or result.get("error", ""), "known": known}
    return {"lab": spend({"start": start}, usage), "current_step": "exp_scout"}


async def design_node(state):
    print("--- EXPERIMENT: DESIGN FROM SCRATCH ---")
    brief, previous = state["experiment_brief"], state.get("lab") or {}
    await report_progress("Designing the experiment: the evaluation first, then what to build and compare")
    existing = WORKSPACES / state["thread_id"]
    workspace = Workspace(existing) if existing.exists() else await asyncio.to_thread(Workspace.create, state["thread_id"])
    sources = "\n".join(f"- {s.get('title')}" for s in (state.get("raw_sources") or [])[:SOURCES_SHOWN])
    task = f"{labs.brief_text(brief)}\n\nResearch sources found so far:\n{sources or 'none'}"
    result, usage = await run_phase("design", "experiment_design", DESIGN, task, _context(brief))
    benchmark = {"read": "json", **(result.get("benchmark") or {}), "protected": result.get("protected") or []}
    lab = {**previous, "mode": BUILD, "frozen": False, "designed": True, "workspace": str(workspace.path),
           "base_commit": workspace.head(), "ready": False, "spec": labs.normalise_spec(benchmark),
           "hypotheses": labs.normalise_hypotheses(result.get("steps"), []),
           "setup": [str(c) for c in result.get("setup") or [] if c], "error": result.get("error", ""),
           "env": {k: result.get(k) for k in ("summary", "risks", "questions")}}
    return {"lab": spend(lab, usage), "notebook": [], "current_step": "exp_design"}


def route_after_launch(state) -> str:
    """A named repository is read straight away; otherwise look for one first."""
    return "exp_understand" if labs.clone_source(state["experiment_brief"].get("target", "")) else "exp_scout"


def route_after_scout(state) -> str:
    return "exp_design" if state["lab"].get("mode") == BUILD else "exp_understand"
