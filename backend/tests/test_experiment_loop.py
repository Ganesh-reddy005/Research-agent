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
import agents.experiment_start as start_mod
from test_api import client, start, THREAD, CONFIG  # noqa: F401
from test_experiments import no_database, resume  # noqa: F401

class FakeBox:
    """A sandbox whose measure prints the number in the workspace's SPEED file."""
    def __init__(self, workspace, **kwargs):
        self.root = workspace
    def run(self, command, timeout=None):
        from sandbox.base import CommandResult
        if (self.root / "RESULTS.json").exists():  # code built from scratch prints a results table
            return CommandResult(command, 0, (self.root / "RESULTS.json").read_text().strip(), "", 0.01)
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
    for mod in (setup_mod, loop_mod):
        monkeypatch.setattr(mod, "DockerSandbox", lambda path, **kw: FakeBox(__import__("pathlib").Path(path)))
    tasks = []
    async def fake_phase(phase, agent_name, system, task, ctx):
        tasks.append((phase, task))
        if phase == "scout":
            return {"starting_point": {"url": str(origin), "why": "it already does this"}, "alternatives": []}, {}
        if phase == "design":
            return {"summary": "Compare two sorts.", "steps": [{"idea": "write the evaluation"}, {"idea": "implement quicksort"},
                                                                {"idea": "implement mergesort"}],
                    "setup": [], "benchmark": {"measure": "python3 evaluate.py", "read": "json", "checks": {"tests": "pytest"}},
                    "protected": ["evaluate.py"]}, {}
        step = task.split("implement: ")[1].split("\n")[0] if phase == "code" else ""
        if step in {"write the evaluation", "implement quicksort", "implement mergesort"}:
            table = {"write the evaluation": {}, "implement quicksort": {"quicksort": {"seconds": 1.5}},
                     "implement mergesort": {"quicksort": {"seconds": 1.5}, "mergesort": {"seconds": 2.0}}}[step]
            if step == "write the evaluation":
                ctx.edits.write_file("evaluate.py", "print('{}')\n")
            ctx.edits.write_file(f"{step.split()[-1]}.py", "# code\n")
            if step == "implement mergesort":  # tries to change the frozen evaluation as well
                assert ctx.edits.write_file("evaluate.py", "print('rigged')\n").startswith("evaluate.py is protected")
                (ctx.code.root / "evaluate.py").write_text("print('rigged')\n")  # as a shell command could
            (ctx.code.root / "RESULTS.json").write_text(__import__("json").dumps(table))  # what the measure would print
            return {"summary": step}, {}
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
    monkeypatch.setattr(start_mod, "run_phase", fake_phase)
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

def test_a_changed_plan_needs_a_direction(client):
    from fastapi import HTTPException
    from api.experiment_actions import experiment_update
    with pytest.raises(HTTPException):
        experiment_update("experiment_decision", {"current_step": "exp_reflect"}, {"decision": "change plan"})
    assert experiment_update("experiment_decision", {"current_step": "exp_reflect"}, {"decision": "stop"}) == \
        {"experiment_decision": {"decision": "stop", "direction": ""}}

def to_brief_pause(http, graph, target="", goal="minimize"):
    start(graph, pauses=3)
    resume(http, "plan_experiments")
    brief = {"objective": "Make it faster", "target": target, "metric": {"name": "seconds", "goal": goal}}
    assert http.put(f"/api/research/{THREAD}/brief", json={"brief": brief}).json()["missing"] == []

def test_without_a_repository_lume_proposes_existing_code_and_the_user_confirms(client, lab):
    http, graph = client
    origin, tasks = lab
    to_brief_pause(http, graph, target="some CPU inference engine")  # a description, not a repository
    resume(http, "launch_experiments")
    snap = state(graph)
    assert snap.values["current_step"] == "exp_scout" and snap.values["lab"]["start"]["url"] == str(origin)
    assert [phase for phase, _ in tasks] == ["scout"]  # nothing is read until the user confirms

    resume(http, "choose_start", {"url": str(origin)})
    snap = state(graph)
    assert snap.values["experiment_brief"]["target"] == str(origin) and snap.values["current_step"] == "exp_plan"
    assert [phase for phase, _ in tasks] == ["scout", "understand", "plan"]

def test_from_scratch_the_evaluation_comes_first_is_frozen_then_variants_are_compared(client, lab, tmp_path):
    http, graph = client
    origin, tasks = lab
    to_brief_pause(http, graph)
    resume(http, "launch_experiments")
    resume(http, "choose_start", {"scratch": True})
    snap = state(graph)
    assert snap.values["lab"]["mode"] == "build" and [h["idea"] for h in snap.values["lab"]["hypotheses"]][0] == "write the evaluation"
    assert [phase for phase, _ in tasks] == ["scout", "design"]  # the design is the plan: no second planning call

    resume(http, "approve_experiment_plan", {"hypotheses": snap.values["lab"]["hypotheses"]})
    snap = state(graph)  # set up, then the evaluation is written straight away (no baseline to measure)
    assert snap.values["current_step"] == "exp_reflect" and snap.values["notebook"][0]["verdict"] == "works"
    assert snap.values["lab"]["frozen"] is False

    resume(http, "experiment_decision", {"decision": "continue"})  # the user has seen the evaluation: freeze it
    snap = state(graph)
    assert snap.values["lab"]["frozen"] is True
    assert snap.values["notebook"][-1]["results"] == {"quicksort.seconds": {"mean": 1.5, "spread": 0.0}}

    resume(http, "experiment_decision", {"decision": "continue"})
    last = state(graph).values["notebook"][-1]
    assert last["verdict"] == "failed checks" and "evaluate.py" in last["log"]  # changing the frozen evaluation fails

    from experiments.lab import results_context
    from experiments.package import code_zip
    values = state(graph).values
    assert "Written from scratch and compared (no baseline)" in results_context(values)
    data, name = code_zip(values)
    import io, zipfile
    files = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert name.startswith("experiment-from-scratch") and "LUME_RUN.md" in files and "quicksort.py" in files
    assert "mergesort.py" not in files  # the download is the latest WORKING version

def test_code_download_includes_the_diff_and_how_to_reproduce(client, lab):
    http, graph = client
    origin, tasks = lab
    to_brief_pause(http, graph, target=str(origin), goal="maximize")
    resume(http, "launch_experiments")
    resume(http, "approve_experiment_plan", {"hypotheses": state(graph).values["lab"]["hypotheses"]})
    resume(http, "experiment_decision", {"decision": "continue"})
    res = http.get(f"/api/research/{THREAD}/code")
    assert res.status_code == 200 and res.headers["content-type"] == "application/zip"
    import io, zipfile
    bundle = zipfile.ZipFile(io.BytesIO(res.content))
    notes = bundle.read("LUME_RUN.md").decode()
    assert "## Measure\n    ./bench" in notes and "#2 [improved] cache the result" in notes
    assert "+150" in bundle.read("changes.diff").decode() and bundle.read("SPEED").decode() == "150\n"

def test_a_failed_design_can_be_tried_again_without_redoing_the_scout(client, lab, monkeypatch):
    http, graph = client
    origin, tasks = lab
    real = start_mod.run_phase
    calls = {"design": 0}
    async def flaky(phase, *args):
        if phase == "design":
            calls["design"] += 1
            if calls["design"] == 1:
                return {"error": "the final answer wasn't valid JSON"}, {}
        return await real(phase, *args)
    monkeypatch.setattr(start_mod, "run_phase", flaky)
    to_brief_pause(http, graph)
    resume(http, "launch_experiments")
    resume(http, "choose_start", {"scratch": True})
    assert state(graph).values["lab"]["error"] and not state(graph).values["lab"]["hypotheses"]

    resume(http, "retry_plan")
    snap = state(graph)
    assert snap.values["current_step"] == "exp_plan" and not snap.values["lab"]["error"]
    assert snap.values["lab"]["hypotheses"][0]["idea"] == "write the evaluation"
    assert [p for p, _ in tasks].count("scout") == 1 and calls["design"] == 2  # only the design ran again

def test_a_question_from_the_agent_reaches_the_user_and_the_answer_reaches_the_agent(client, lab, monkeypatch):
    http, graph = client
    from langgraph.types import interrupt
    real = start_mod.run_phase
    async def asking(phase, *args):
        if phase == "design":  # like the ask_user tool: pause until the user answers
            answer = interrupt({"question": "Include the built-in sort as a reference?"})
            steps = [{"idea": "write the evaluation"}, {"idea": "implement quicksort"}]
            if answer.lower().startswith("yes"):
                steps.append({"idea": "add the built-in sort as a reference"})
            return {"summary": "s", "steps": steps, "benchmark": {"measure": "python3 evaluate.py", "read": "json"}}, {}
        return await real(phase, *args)
    monkeypatch.setattr(start_mod, "run_phase", asking)
    to_brief_pause(http, graph)
    resume(http, "launch_experiments")
    body = resume(http, "choose_start", {"scratch": True})
    assert '"question": "Include the built-in sort as a reference?"' in body
    assert http.get(f"/api/research/{THREAD}").json()["question"] == "Include the built-in sort as a reference?"

    res = http.post("/api/research/resume", json={"thread_id": THREAD, "action": "answer_question", "data": {"answer": " "}})
    assert res.status_code == 400  # an empty answer is refused
    resume(http, "answer_question", {"answer": "Yes, as a reference point"})
    snap = state(graph)
    assert snap.values["current_step"] == "exp_plan"
    assert [h["idea"] for h in snap.values["lab"]["hypotheses"]][-1] == "add the built-in sort as a reference"
    assert http.get(f"/api/research/{THREAD}").json()["question"] == ""

def test_from_scratch_a_failed_step_is_retried_with_its_error_and_nothing_freezes_until_it_works(client, lab, monkeypatch):
    http, graph = client
    origin, tasks = lab
    real = start_mod.run_phase
    tries = {"n": 0}
    async def first_eval_broken(phase, agent_name, system, task, ctx):
        if phase == "code" and "write the evaluation" in task:
            tries["n"] += 1
            if tries["n"] == 1:  # puts the tests in the wrong place: the check fails
                tasks.append((phase, task))
                ctx.edits.write_file("evaluate.py", "print('{}')\n")
                return {"summary": "wrote it"}, {}
        return await real(phase, agent_name, system, task, ctx)
    monkeypatch.setattr(start_mod, "run_phase", first_eval_broken)
    monkeypatch.setattr(loop_mod, "run_phase", first_eval_broken)
    from sandbox.base import CommandResult
    def run(self, command, timeout=None):  # the tests check fails until the evaluation step has really been written
        if "pytest" in command and not (self.root / "evaluation.py").exists():
            return CommandResult(command, 1, "", "no tests ran", 0.01)
        return CommandResult(command, 0, (self.root / "RESULTS.json").read_text() if (self.root / "RESULTS.json").exists() else "{}", "", 0.01)
    monkeypatch.setattr(FakeBox, "run", run)
    to_brief_pause(http, graph)
    resume(http, "launch_experiments")
    resume(http, "choose_start", {"scratch": True})
    resume(http, "approve_experiment_plan", {"hypotheses": state(graph).values["lab"]["hypotheses"]})
    snap = state(graph)
    assert snap.values["notebook"][0]["verdict"] == "failed checks"
    assert "Check 'tests': pytest" in tasks[-1][1] and "Measure: python3 evaluate.py" in tasks[-1][1]  # it saw the commands

    resume(http, "experiment_decision", {"decision": "continue"})
    snap = state(graph)
    assert snap.values["lab"]["frozen"] is False  # the evaluation never worked: nothing to freeze
    assert snap.values["notebook"][-1]["hypothesis"] == "write the evaluation"  # the same step again, not the next one
    assert "This step was tried before and failed" in tasks[-1][1]
