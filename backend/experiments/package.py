"""The experiment's code as a download: the final (or best) version, plus LUME_RUN.md with everything
needed to reproduce the results: where the code started, setup, the exact commands, and the results.
Improving existing code also includes changes.diff against the starting point."""
import io
import zipfile
from experiments import lab as labs
from experiments import notebook as nb
from experiments.workspace import Workspace


def _commands(lab: dict) -> str:
    spec = lab.get("spec") or {}
    lines = ["## Setup (run once, with network)", *(f"    {c}" for c in lab.get("setup") or ["(none)"]), ""]
    if spec.get("build"):
        lines += ["## Build", f"    {spec['build']}", ""]
    lines += ["## Checks (each must exit 0)", *(f"    {c}    # {name}" for name, c in (spec.get("checks") or {}).items()), "",
              "## Measure", f"    {spec.get('measure', '')}",
              f"Read as: {spec.get('read', '')}; {spec.get('repeats', '')} repeats after {spec.get('warmup', '')} warm-up runs.", ""]
    return "\n".join(lines)


def run_notes(state) -> str:
    brief, lab, notebook = state["experiment_brief"], state.get("lab") or {}, state.get("notebook") or []
    start = ("Written from scratch by Lume's coding agent." if lab.get("mode") == "build" else
             f"Starting point: {brief.get('target')} at commit {lab.get('base_commit', '')}.")
    return "\n".join([
        "# How to reproduce these results", "", f"Objective: {brief['objective']}", start,
        f"Metric: {brief['metric']['name']} ({'higher' if brief['metric']['goal'] == 'maximize' else 'lower'} is better)", "",
        "Lume ran every command below in a Debian container (python3, build-essential, cmake), with no network after setup.", "",
        _commands(lab), "## Attempts", nb.render(notebook, brief["metric"]["goal"]), "",
    ])


def code_zip(state) -> tuple[bytes, str]:
    """(zip bytes, file name): the best (improving) or latest working (from scratch) version of the code."""
    lab = state.get("lab") or {}
    workspace = Workspace(lab["workspace"])
    commit = lab.get("best_commit") or workspace.head()
    archive = workspace.git_bytes("archive", "--format=zip", commit)
    buffer = io.BytesIO(archive)
    with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("LUME_RUN.md", run_notes(state))
        if lab.get("mode") != "build" and commit != lab.get("base_commit"):
            bundle.writestr("changes.diff", workspace.git("diff", lab["base_commit"], commit))
    name = "experiment-from-scratch" if lab.get("mode") == "build" else workspace.path.name
    return buffer.getvalue(), f"{name}-{commit[:8]}.zip"
