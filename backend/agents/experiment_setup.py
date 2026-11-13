"""Coding agent, before any attempt: understand the target, plan the hypotheses (the user approves the
plan, setup commands and benchmark), then install dependencies once and measure the baseline."""
import asyncio
from experiments import lab as labs
from experiments import notebook as nb
from experiments.agent_runtime import run_phase
from experiments.code_tools import CodeTools
from experiments.harness import BenchmarkSpec, run_attempt
from experiments.prompts import PLAN, UNDERSTAND
from experiments.toolbox import ToolContext
from experiments.workspace import Workspace
from sandbox.base import Limits
from sandbox.docker_sandbox import DockerSandbox
from utils.costs import cost_usd, tokens
from utils.events import report_progress

SETUP_LIMITS = Limits(network=True, timeout=900)
LOG_CHARS = 1500


def spend(lab: dict, usage: dict) -> dict:
    return {**lab, "cost_usd": round(lab.get("cost_usd", 0) + cost_usd(usage), 4), "tokens": lab.get("tokens", 0) + tokens(usage)}


async def understand_node(state):
    print("--- EXPERIMENT: UNDERSTAND ---")
    brief = state["experiment_brief"]
    await report_progress("Getting a copy of the target code")
    workspace = await asyncio.to_thread(labs.open_workspace, brief["target"], state["thread_id"])
    code = await asyncio.to_thread(CodeTools, workspace.path)
    await report_progress(f"Reading the code: {len(code.graph.files)} source files")
    ctx = ToolContext(code=code, target=brief["target"], goal=brief["metric"]["goal"])
    result, usage = await run_phase("understand", "experiment_understand", UNDERSTAND, labs.brief_text(brief), ctx)
    spec = labs.normalise_spec({**(result.get("benchmark") or {}), "protected": result.get("protected") or []})
    lab = {**(state.get("lab") or {}), "mode": "improve", "frozen": True,  # protected files apply from the start
           "workspace": str(workspace.path), "base_commit": workspace.head(), "ready": False, "hypotheses": [],
           "env": labs.normalise_env(result),
           "setup": [str(c) for c in result.get("setup") or [] if c], "spec": spec, "error": result.get("error", ""),
           "phases": {"understand": phase_record(result)}}
    return {"lab": spend(lab, usage), "notebook": [], "current_step": "exp_understand"}


def phase_record(result: dict) -> dict:
    """What a phase did, kept for the plan screen: its tool calls, and how it ended if not cleanly."""
    return {"trace": result.get("trace", []), "note": str(result.get("note") or result.get("error") or "")}


async def plan_node(state):
    print("--- EXPERIMENT: PLAN ---")
    brief, lab, notebook = state["experiment_brief"], state["lab"], state.get("notebook", [])
    direction = (state.get("experiment_decision") or {}).get("direction", "")
    if lab.get("designed") and not direction:  # a design from scratch already holds the plan: don't pay for another
        return {"lab": {**lab, "designed": False, "approved": False}, "experiment_decision": {}, "current_step": "exp_plan"}
    await report_progress("Checking what was already tried, then ranking ideas")
    code = await asyncio.to_thread(CodeTools, lab["workspace"])
    ctx = ToolContext(code=code, target=brief["target"], goal=brief["metric"]["goal"], notebook=notebook)
    result, usage = await run_phase("plan", "experiment_plan", PLAN, labs.plan_task(brief, lab, notebook, direction), ctx)
    hypotheses = labs.normalise_hypotheses(result.get("hypotheses"), lab.get("hypotheses", []))
    lab = {**lab, "hypotheses": hypotheses, "plan_notes": str(result.get("notes", "")), "approved": False,
           "error": result.get("error", "") if not hypotheses else "",
           "phases": {**(lab.get("phases") or {}), "plan": phase_record(result)}}
    return {"lab": spend(lab, usage), "experiment_decision": {}, "current_step": "exp_plan"}


def _setup_and_measure(lab: dict, thread_id: str, goal: str) -> tuple[dict, dict]:
    """Install dependencies (network on, saved as the task's image), then measure the unmodified code."""
    workspace, spec = Workspace(lab["workspace"]), BenchmarkSpec.from_dict(lab["spec"])
    image = f"lume-task:{thread_id[:12]}"
    workspace.reset(lab["base_commit"])
    with DockerSandbox(workspace.path, setup=True, limits=SETUP_LIMITS, save_as=image) as box:
        for command in lab.get("setup", []):
            out = box.run(command)
            if not out.ok:
                failed = {"checks": {"setup": False}, "metric": None, "spread": None, "stage": "setup",
                          "error": f"setup command failed: {command}", "log": out.tail(LOG_CHARS)}
                return {**lab, "image": ""}, failed
    if lab.get("mode") == "build":  # nothing to measure yet: the first step writes the evaluation
        return {**lab, "image": image}, None
    with DockerSandbox(workspace.path, image=image) as box:
        return {**lab, "image": image}, run_attempt(box, spec)


async def setup_node(state):
    print("--- EXPERIMENT: SETUP AND BASELINE ---")
    brief, lab = state["experiment_brief"], state["lab"]
    await report_progress("Installing dependencies and measuring the unmodified code (the baseline)")
    lab, result = await asyncio.to_thread(_setup_and_measure, lab, state["thread_id"], brief["metric"]["goal"])
    if result is None:  # built from scratch: ready to write the first step
        return {"lab": {**lab, "ready": True, "best_commit": lab["base_commit"]}, "current_step": "exp_setup"}
    entry = nb.record([], brief["metric"]["goal"], nb.BASELINE_NAME, "none", result["checks"], result["metric"],
                      spread=result["spread"] or 0.0)
    entry.update(commit=lab["base_commit"], stage=result["stage"], error=result["error"], log=result["log"][-LOG_CHARS:])
    ready = entry["verdict"] == nb.BASELINE
    lab = {**lab, "ready": ready, "best_commit": lab["base_commit"] if ready else None}
    return {"lab": lab, "notebook": [entry] if ready else [], "last_attempt": entry, "current_step": "exp_setup"}
