"""The coding agent's whole loop through the API, offline: launch, plan approval, setup and baseline,
an attempt after each decision, a changed plan, and stopping to write the paper with the results.
Models and Docker are fakes; git, the harness, the notebook and the graph are real."""
import asyncio
import json
import subprocess
import pytest
from langchain_core.messages import AIMessage
import agents.experiment_setup as setup_mod
import agents.experiment_loop as loop_mod
from test_api import client, start, THREAD, CONFIG  # noqa: F401
from test_experiments import no_database, resume  # noqa: F401

class FakeBox:
    """A sandbox whose measure prints the number in the workspace's SPEED file."""
    def __init__(self, workspace, **kwargs):
        self.root = workspace
    def run(self, command, timeout=None):
        from sandbox.base import CommandResult
        speed = (self.root / "SPEED").read_text().strip() if (self.root / "SPEED").exists() else "0"
        return CommandResult(command, 0, f"speed {speed}", "", 0.01)
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass

@pytest.fixture
def lab(tmp_path, monkeypatch):
    origin = tmp_path / "origin"
    origin.mkdir()
    subprocess.run(["git", "init", "-q", str(origin)], check=True)
    (origin / "SPEED").write_text("100\n")
    (origin / "engine.py").write_text("def run():\n    return 1\n")
    subprocess.run(["git", "-C", str(origin), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(origin), "-c", "user.name=x", "-c", "user.email=x@x", "commit", "-qm", "init"], check=True)
    monkeypatch.setattr("experiments.workspace.WORKSPACES", tmp_path / "ws")
    monkeypatch.setattr("experiments.lab.WORKSPACES", tmp_path / "ws")
    for mod in (setup_mod, loop_mod):
        monkeypatch.setattr(mod, "DockerSandbox", lambda path, **kw: FakeBox(__import__("pathlib").Path(path)))
    tasks = []
    async def fake_phase(phase, agent_name, system, task, ctx):
        tasks.append((phase, task))
        if phase == "understand":
            return {"summary": "A tiny engine.", "key_files": ["engine.py"], "setup": ["pip install nothing"],
                    "benchmark": {"measure": "./bench", "read": "regex:speed (\\d+)", "checks": {"tests": "pytest"}, "repeats": 2},
                    "protected": ["tests/*"]}, {}
        if phase == "plan":
            return {"hypotheses": [{"idea": "cache the result", "why": "repeated work"},
                                   {"idea": "unroll the loop", "why": "fewer branches"}]}, {}
        speed = {"cache the result": "150", "unroll the loop": "90", "use a lookup table": "160"}[task.split("implement: ")[1].split("\n")[0]]
        ctx.edits.write_file("SPEED", speed + "\n")
        return {"summary": f"set speed to {speed}"}, {"some-model": {"input_tokens": 1000, "output_tokens": 100}}
    monkeypatch.setattr(setup_mod, "run_phase", fake_phase)
    monkeypatch.setattr(loop_mod, "run_phase", fake_phase)
    async def fake_reflect(messages, agent_name=None, **kw):
        return AIMessage(content=json.dumps({"findings": "It went as reported.", "lesson": "noted", "next": "keep going",
                                             "recommend": "continue"}))
    monkeypatch.setattr(loop_mod, "ainvoke_llm", fake_reflect)
    return origin, tasks

def state(graph):
    return asyncio.run(graph.aget_state(CONFIG))

def test_the_loop_reports_after_every_attempt_and_the_user_decides(client, lab):
    http, graph = client
    origin, tasks = lab
    start(graph, pauses=3)
    resume(http, "plan_experiments")
    brief = {"objective": "Make the engine faster", "target": str(origin), "metric": {"name": "speed", "goal": "maximize"}}
    assert http.put(f"/api/research/{THREAD}/brief", json={"brief": brief}).json()["missing"] == []

    resume(http, "launch_experiments")  # understand, then plan, then pause for approval
    snap = state(graph)
    assert snap.values["current_step"] == "exp_plan" and snap.next == ("exp_setup",)
    assert [h["idea"] for h in snap.values["lab"]["hypotheses"]] == ["cache the result", "unroll the loop"]

    resume(http, "approve_experiment_plan", {"hypotheses": snap.values["lab"]["hypotheses"],
                                             "spec": {**snap.values["lab"]["spec"], "repeats": 3}})
    snap = state(graph)  # setup + baseline, then a report
    assert snap.values["current_step"] == "exp_reflect"
    assert [(a["n"], a["verdict"], a["metric"]) for a in snap.values["notebook"]] == [(1, "baseline", 100.0)]
    assert snap.values["lab"]["spec"]["repeats"] == 3  # the user's edit to the benchmark was kept

    resume(http, "experiment_decision", {"decision": "continue"})
    snap = state(graph)
    assert [(a["verdict"], a["metric"]) for a in snap.values["notebook"]] == [("baseline", 100.0), ("improved", 150.0)]
    assert snap.values["notebook"][-1]["files"] == ["SPEED"] and snap.values["lab"]["report"]["findings"]

    resume(http, "experiment_decision", {"decision": "continue"})  # the second idea makes it worse
    snap = state(graph)
    assert snap.values["notebook"][-1]["verdict"] == "worse"
    assert snap.values["lab"]["best_commit"] == snap.values["notebook"][1]["commit"]  # best stays attempt #2

    resume(http, "experiment_decision", {"decision": "change plan", "direction": "try a lookup table"})
    assert "The user's direction for the next attempts: try a lookup table" in tasks[-1][1]
    planned = state(graph).values["lab"]["hypotheses"]
    assert [h["status"] for h in planned] == ["done", "done", "pending", "pending"]  # attempted ideas are kept
    planned[2]["idea"] = "use a lookup table"
    resume(http, "approve_experiment_plan", {"hypotheses": planned})
    snap = state(graph)
    assert snap.values["notebook"][-1]["hypothesis"] == "use a lookup table"
    assert (origin / "SPEED").read_text() == "100\n"  # the original repository is never touched

    body = resume(http, "experiment_decision", {"decision": "stop"})
    assert "event: done" in body
    final = state(graph).values
    assert final["final_report"] and len(final["notebook"]) == 4
    from experiments.lab import results_context
    results = results_context(final)  # what the synthesis and writer agents are given
    assert "Best result: attempt #4, +60.0% speed versus the baseline." in results
    assert "#3 [worse] unroll the loop" in results  # failures are reported too

def test_launch_needs_a_complete_brief_with_a_cloneable_target(client, lab):
    http, graph = client
    start(graph, pauses=3)
    resume(http, "plan_experiments")
    http.put(f"/api/research/{THREAD}/brief", json={"brief": {"objective": "o", "target": "a description, not a repo",
                                                               "metric": {"name": "m"}}})
    res = http.post("/api/research/resume", json={"thread_id": THREAD, "action": "launch_experiments", "data": {}})
    assert res.status_code == 400 and "repository URL" in res.json()["detail"]
    res = http.post("/api/research/resume", json={"thread_id": THREAD, "action": "experiment_decision", "data": {"decision": "stop"}})
    assert res.status_code == 409  # not waiting for that

def test_a_changed_plan_needs_a_direction(client):
    from fastapi import HTTPException
    from api.experiment_actions import experiment_update
    with pytest.raises(HTTPException):
        experiment_update("experiment_decision", {"current_step": "exp_reflect"}, {"decision": "change plan"})
    assert experiment_update("experiment_decision", {"current_step": "exp_reflect"}, {"decision": "stop"}) == \
        {"experiment_decision": {"decision": "stop", "direction": ""}}
