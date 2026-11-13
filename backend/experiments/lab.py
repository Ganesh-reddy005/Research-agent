"""The experiment's working state between phases (the "lab"), and the task text each phase is given.

lab = {"workspace", "base_commit", "best_commit", "image", "ready", "env", "setup", "spec",
       "hypotheses": [{"id", "idea", "why", "expected_gain", "cost", "files", "status"}],
       "approved", "error", "report", "cost_usd", "tokens"}"""
import re
from pathlib import Path
from experiments import notebook as nb
from experiments.harness import BenchmarkSpec, TIME
from experiments.workspace import Workspace, workspace_path

PENDING, DONE = "pending", "done"
_URL = re.compile(r"(https?://\S+|git@\S+)")


def clone_source(target: str) -> str | None:
    """What git can clone from the brief's target: a URL in it, or a local git folder."""
    match = _URL.search(target or "")
    if match:
        return match.group(1).rstrip(".,;)")
    path = Path((target or "").strip()).expanduser()
    return str(path) if (path / ".git").exists() else None


def open_workspace(target: str, name: str) -> Workspace:
    """The session's workspace, cloned on first use."""
    existing = workspace_path(name)
    if existing.exists():
        return Workspace(existing)
    source = clone_source(target)
    if not source:
        raise ValueError("The brief's target must be a repository URL or a local git folder")
    return Workspace.clone(source, name)


def normalise_spec(raw) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    checks = raw.get("checks") if isinstance(raw.get("checks"), dict) else {}
    def number(key, default, low, high):
        try:
            return min(max(int(raw.get(key, default)), low), high)
        except (TypeError, ValueError):
            return default
    return BenchmarkSpec(measure=str(raw.get("measure") or ""), read=str(raw.get("read") or TIME),
                         build=str(raw.get("build") or ""), checks={str(k): str(v) for k, v in checks.items() if v},
                         repeats=number("repeats", 5, 2, 20), warmup=number("warmup", 1, 0, 5),
                         timeout=number("timeout", 600, 30, 3600),
                         protected=tuple(str(g) for g in raw.get("protected") or () if g)).to_dict()


def normalise_hypotheses(raw, earlier: list[dict]) -> list[dict]:
    """The attempted hypotheses stay (from earlier, never from raw, so an edited plan sent back whole can't
    queue them again); the new plan's ideas follow them as pending."""
    kept = [h for h in earlier if h.get("status") == DONE]
    fresh = [h for h in (raw if isinstance(raw, list) else [])
             if isinstance(h, dict) and str(h.get("idea", "")).strip() and h.get("status") != DONE]
    return kept + [{"id": len(kept) + i + 1, "idea": str(h["idea"]).strip(), "why": str(h.get("why", "")),
                    "expected_gain": str(h.get("expected_gain", "")), "cost": str(h.get("cost", "")),
                    "files": [str(f) for f in h.get("files") or []][:8], "status": PENDING}
                   for i, h in enumerate(fresh)]


def next_hypothesis(lab: dict) -> dict | None:
    return next((h for h in lab.get("hypotheses", []) if h.get("status") == PENDING), None)


def attempts_left(state) -> int:
    used = sum(1 for a in state.get("notebook", []) if a.get("hypothesis") != nb.BASELINE_NAME)
    return max(state["experiment_brief"].get("attempt_limit", 5) - used, 0)


def brief_text(brief: dict) -> str:
    metric = brief["metric"]
    lines = [f"Objective: {brief['objective']}", f"Target: {brief['target']}",
             f"Metric: {metric['name']} ({'higher' if metric['goal'] == 'maximize' else 'lower'} is better)"
             + (f", measured by {metric['measured_by']}" if metric.get("measured_by") else ""),
             f"Baseline: {brief.get('baseline') or 'the unmodified code'}"]
    for label, key in [("Must still hold", "must_hold"), ("Must not change", "off_limits"), ("Notes from the user", "notes")]:
        if brief.get(key):
            lines.append(f"{label}:\n" + "\n".join(f"- {item}" for item in brief[key]))
    return "\n".join(lines)


def code_task(brief: dict, lab: dict, hypothesis: dict, notebook: list[dict]) -> str:
    """What the coding phase is told: the brief, the exact commands that will grade its work, the idea,
    and, when it retries a step, what went wrong last time."""
    spec = lab.get("spec") or {}
    grading = [f"Build: {spec['build']}" if spec.get("build") else "Build: none",
               *(f"Check '{name}': {command}" for name, command in (spec.get("checks") or {}).items()),
               f"Measure: {spec.get('measure', '')} (read as {spec.get('read', '')})"]
    if spec.get("read") == "json":
        grading.append("The measure command must print ONE line of JSON on its last line: {\"variant\": {\"metric\": number}}")
    parts = [brief_text(brief), "Your work is graded from the working directory with exactly these commands:\n" + "\n".join(grading),
             f"Protected files (read-only): {', '.join(spec.get('protected') or []) or 'none'}" if lab.get("frozen", True) else
             "The evaluation is not frozen yet: you are writing it, so the files above may be created.",
             f"Hypothesis to implement: {hypothesis['idea']}\nWhy: {hypothesis.get('why', '')}"]
    earlier = [a for a in notebook if a.get("hypothesis") == hypothesis["idea"]]
    if earlier:
        last = earlier[-1]
        parts.append(f"This step was tried before and failed ({last.get('error') or last.get('verdict')}). Log:\n"
                     f"{(last.get('log') or '')[-800:]}\nFix that cause this time.")
    return "\n\n".join(parts)


def plan_task(brief: dict, lab: dict, notebook: list[dict], direction: str) -> str:
    env = lab.get("env") or {}
    parts = [brief_text(brief), f"What the code is: {env.get('summary', '')}",
             f"Key files: {', '.join(env.get('key_files', []))}", f"Lab notebook:\n{nb.render(notebook, brief['metric']['goal'])}"]
    if direction:
        parts.append(f"The user's direction for the next attempts: {direction}")
    return "\n\n".join(parts)


def latest_results(notebook: list[dict]) -> dict:
    """The results table of the latest working step: every variant built so far."""
    working = [a for a in notebook if a.get("verdict") == nb.WORKS and a.get("results")]
    return working[-1]["results"] if working else {}


def results_context(state) -> str:
    """The experiments, for the paper's writers: real runs, to be reported exactly, failures included."""
    notebook = state.get("notebook") or []
    if not notebook:
        return ""
    brief, lab = state["experiment_brief"], state.get("lab") or {}
    spec = lab.get("spec") or {}
    goal = brief["metric"]["goal"]
    if lab.get("mode") == "build":
        table = "\n".join(f"- {name}: {v['mean']:.4g} ± {v['spread']:.2g}" for name, v in latest_results(notebook).items())
        summary = ("Written from scratch and compared (no baseline). Results of the final code, mean ± spread over "
                   f"{spec.get('repeats', '')} runs:\n{table or 'none'}\n")
    else:
        best, baseline = nb.best_attempt(notebook, goal), notebook[0].get("metric")
        summary = ""
        if best and baseline and best["n"] != 1:
            change = (best["metric"] - baseline) / baseline * 100
            summary = f"Best result: attempt #{best['n']}, {change:+.1f}% {brief['metric']['name']} versus the baseline.\n"
        start = (lab.get("start") or {}).get("url") or brief.get("target", "")
        summary = f"Starting point: {start} at commit {str(lab.get('base_commit', ''))[:12]}.\n" + summary
    return f"""EXPERIMENTS (real runs executed by Lume's coding agent in an isolated sandbox; report these numbers
exactly, include attempts that failed or made things worse, and never add results that are not listed):
Metric: {brief['metric']['name']} ({'higher' if goal == 'maximize' else 'lower'} is better),
measured with: {spec.get('measure', '')} ({spec.get('repeats', '')} repeats after {spec.get('warmup', '')} warm-up runs).
Checks every attempt had to pass: {', '.join(spec.get('checks', {})) or 'none'}.
{summary}Attempts:
{nb.render(notebook, goal)}"""
