"""Coding agent, the loop: one attempt (code, then grading in a fresh sandbox), a plain report, and a
pause for the user: continue, change the plan, or stop and write the paper."""
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from agents.experiment_setup import LOG_CHARS, spend
from experiments import lab as labs
from experiments import notebook as nb
from experiments.agent_runtime import run_phase
from experiments.brief import json_object
from experiments.code_tools import CodeTools
from experiments.edit_tools import EditTools
from experiments.harness import RESULTS, BenchmarkSpec, run_attempt
from experiments.prompts import CODE, REFLECT
from experiments.toolbox import ToolContext
from experiments.workspace import Workspace
from sandbox.docker_sandbox import DockerSandbox
from utils.costs import cost_usd, tokens
from utils.events import report_progress
from utils.llm import ainvoke_llm

CONTINUE, REVISE, STOP = "continue", "change plan", "stop"


def _spec(lab: dict) -> BenchmarkSpec:
    """The approved benchmark; before a from-scratch evaluation is frozen, its files are still being written."""
    return BenchmarkSpec.from_dict(lab["spec"] if lab.get("frozen", True) else {**lab["spec"], "protected": []})


def _grade(lab: dict, commit: str, changed: list[str]) -> dict:
    """The full benchmark in a fresh sandbox the agent never touched."""
    with DockerSandbox(lab["workspace"], image=lab["image"]) as box:
        return run_attempt(box, _spec(lab), changed=changed)


async def attempt_node(state):
    print("--- EXPERIMENT: ATTEMPT ---")
    brief, lab, notebook = state["experiment_brief"], state["lab"], state.get("notebook", [])
    hypothesis, goal = labs.next_hypothesis(lab), brief["metric"]["goal"]
    workspace, spec = Workspace(lab["workspace"]), _spec(lab)
    await asyncio.to_thread(workspace.reset, lab["best_commit"])  # every attempt starts from the best so far
    await report_progress(f"Attempt {len(notebook) + (lab.get('mode') == 'build')}: {hypothesis['idea']}")
    code = await asyncio.to_thread(CodeTools, workspace.path)
    box = await asyncio.to_thread(DockerSandbox, workspace.path, image=lab["image"])
    try:
        ctx = ToolContext(code=code, target=brief["target"], goal=goal, notebook=notebook, edits=EditTools(code, box, spec))
        task = f"{labs.brief_text(brief)}\n\nHypothesis to implement: {hypothesis['idea']}\nWhy: {hypothesis.get('why', '')}"
        result, usage = await run_phase("code", "experiment_code", CODE, task, ctx)
    finally:
        await asyncio.to_thread(box.close)
    commit = await asyncio.to_thread(workspace.snapshot, f"attempt {len(notebook)}: {hypothesis['idea']}"[:200])
    changed = await asyncio.to_thread(workspace.changed_files, lab["best_commit"], commit)
    await report_progress("Grading: build, checks, then the full benchmark in a fresh sandbox")
    graded = (await asyncio.to_thread(_grade, lab, commit, changed) if changed else
              {"checks": {}, "metric": None, "spread": None, "stage": "code", "error": "no code was changed", "log": ""})
    entry = nb.record(notebook, goal, hypothesis["idea"], result.get("summary", ""), graded["checks"], graded["metric"],
                      spread=graded["spread"] or 0.0, cost_usd=cost_usd(usage),
                      results=graded.get("results") if spec.read == RESULTS and not graded["error"] else
                      ({} if spec.read == RESULTS else None))
    entry.update(commit=commit, files=changed, stage=graded["stage"], error=graded["error"] or result.get("error", ""),
                 log=graded["log"][-LOG_CHARS:], tokens=tokens(usage))
    hypotheses = [{**h, "status": labs.DONE, "attempt": entry["n"]} if h["id"] == hypothesis["id"] else h for h in lab["hypotheses"]]
    best = commit if entry["verdict"] in (nb.IMPROVED, nb.WORKS) else lab["best_commit"]
    lab = spend({**lab, "hypotheses": hypotheses, "best_commit": best}, usage)
    return {"lab": lab, "notebook": notebook + [entry], "last_attempt": entry, "current_step": "exp_attempt"}


async def reflect_node(state):
    print("--- EXPERIMENT: REPORT ---")
    brief, lab, notebook = state["experiment_brief"], state["lab"], state.get("notebook", [])
    attempt, goal = state.get("last_attempt") or {}, brief["metric"]["goal"]
    pending = [h["idea"] for h in lab.get("hypotheses", []) if h.get("status") == labs.PENDING]
    facts = (f"{labs.brief_text(brief)}\n\nLab notebook:\n{nb.render(notebook, goal)}\n\nThis attempt: {attempt.get('hypothesis')}"
             f"\nVerdict: {attempt.get('verdict')}; stage reached: {attempt.get('stage')}; error: {attempt.get('error') or 'none'}"
             f"\nWhat the agent changed: {attempt.get('change') or 'n/a'}; files: {', '.join(attempt.get('files', [])) or 'none'}"
             f"\nLog tail:\n{attempt.get('log', '')[-800:]}\n\nIdeas still planned: {'; '.join(pending) or 'none'}"
             f"\nAttempts left: {labs.attempts_left(state)}"
             + ("\nThis experiment builds code from scratch: there is no baseline. Report the results table, and say "
                "whether differences between variants are larger than their spread."
                + ("" if lab.get("frozen") else " The evaluation is not frozen yet: ask the user to review it, since "
                   "continuing freezes it.") if lab.get("mode") == "build" else ""))
    response = await ainvoke_llm([SystemMessage(content=REFLECT), HumanMessage(content=facts)], agent_name="experiment_reflect")
    report = json_object(response.content) or {"findings": response.content.strip()[:1500]}
    usage = response.usage_metadata or {}
    lab = spend(lab, {response.response_metadata.get("model_name", "?"): usage} if usage else {})
    notebook = [*notebook[:-1], {**notebook[-1], "lesson": str(report.get("lesson", ""))}] if notebook else notebook
    report = {**report, "attempt": attempt.get("n"), "attempts_left": labs.attempts_left(state), "pending": pending}
    return {"lab": {**lab, "report": report}, "notebook": notebook, "current_step": "exp_reflect"}


def route_after_plan(state) -> str:
    return "exp_attempt" if state["lab"].get("ready") else "exp_setup"


def route_after_setup(state) -> str:
    """From scratch there is no baseline to report: once set up, the first step starts. Failures are reported."""
    lab = state["lab"]
    return "exp_attempt" if lab.get("mode") == "build" and lab.get("ready") else "exp_reflect"


def route_after_report(state) -> str:
    """The user's decision; continuing with no ideas left means planning again, and no attempts left means stopping."""
    lab, decision = state["lab"], (state.get("experiment_decision") or {}).get("decision", CONTINUE)
    if decision == STOP or (lab.get("ready") and labs.attempts_left(state) == 0):
        return "synthesis"
    if decision == REVISE or not lab.get("ready") or labs.next_hypothesis(lab) is None:
        return "exp_plan"
    return "exp_attempt"
