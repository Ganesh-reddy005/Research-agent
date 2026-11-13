"""The benchmark harness, the git workspace and (when Docker is running) the real sandbox."""
import json
import subprocess
import pytest
from experiments.harness import BenchmarkSpec, read_number, run_attempt
from experiments.workspace import Workspace
from sandbox.base import CommandResult, Limits

class FakeBox:
    """Answers commands from a script: {substring of the command: (exit code, stdout)}."""
    def __init__(self, script):
        self.script, self.ran = script, []
    def run(self, command, timeout=None):
        self.ran.append(command)
        code, out = next((v for k, v in self.script.items() if k in command), (0, ""))
        return CommandResult(command, code, out, "", 0.1)

def test_numbers_are_read_from_json_or_a_pattern():
    assert read_number('log line\n{"results": {"tps": 41.5}}', "json:results.tps") == 41.5
    assert read_number('{"runs": [{"auc": 0.91}]}', "json:runs.0.auc") == 0.91
    assert read_number("throughput: 12.5 tok/s", r"regex:throughput: ([\d.]+)") == 12.5
    assert read_number("nothing here", r"regex:([\d.]+) tok") is None
    assert read_number("not json", "json:x") is None

def test_a_broken_build_never_reaches_the_checks_or_the_benchmark():
    box = FakeBox({"make": (2, "error: expected ';'")})
    spec = BenchmarkSpec(measure="./bench", read="regex:(\\d+)", build="make", checks={"tests": "make test"})
    result = run_attempt(box, spec)
    assert result["stage"] == "build" and result["error"] == "the build failed" and "expected ';'" in result["log"]
    assert box.ran == ["make"]

def test_a_failed_check_stops_before_measuring():
    box = FakeBox({"pytest": (1, "1 failed")})
    spec = BenchmarkSpec(measure="./bench", read="regex:(\\d+)", checks={"unit tests": "pytest", "lint": "ruff ."})
    result = run_attempt(box, spec)
    assert result["checks"] == {"unit tests": False} and result["error"] == "check failed: unit tests"
    assert not any("bench" in c for c in box.ran)

def test_printed_metrics_are_repeated_after_warmup_and_summarised():
    values = iter(["score 9", "score 10", "score 12", "score 11"])  # quick run, warm-up, then two runs
    class Box(FakeBox):
        def run(self, command, timeout=None):
            self.ran.append(command)
            return CommandResult(command, 0, next(values), "", 0.1)
    spec = BenchmarkSpec(measure="./bench", read="regex:score (\\d+)", repeats=2, warmup=1)
    result = run_attempt(Box({}), spec)
    assert result["stage"] == "done" and result["samples"] == [12.0, 11.0]
    assert result["metric"] == 11.5 and round(result["spread"], 3) == 0.707

def test_quick_mode_stops_after_one_measurement():
    box = FakeBox({"./bench": (0, "score 7")})
    result = run_attempt(box, BenchmarkSpec(measure="./bench", read="regex:score (\\d+)"), quick=True)
    assert result["metric"] == 7.0 and len(box.ran) == 1

def test_timings_come_from_hyperfine():
    report = json.dumps({"results": [{"times": [0.30, 0.32, 0.31], "mean": 0.31}]})
    box = FakeBox({"hyperfine": (0, report)})
    result = run_attempt(box, BenchmarkSpec(measure="./bench --size 1000", repeats=3, warmup=1))
    assert result["stage"] == "done" and result["samples"] == [0.30, 0.32, 0.31]
    assert "--warmup 1 --runs 3" in box.ran[-1] and "'./bench --size 1000'" in box.ran[-1]

def test_a_measure_without_the_metric_is_an_error_not_a_zero():
    result = run_attempt(FakeBox({"./bench": (0, "done")}), BenchmarkSpec(measure="./bench", read="json:score"))
    assert result["metric"] is None and result["error"] == "no json:score value in the measure output"

def test_spec_round_trips_through_state():
    spec = BenchmarkSpec(measure="m", build="b", checks={"t": "c"})
    assert BenchmarkSpec.from_dict({**spec.to_dict(), "unknown": 1}) == spec

def test_workspace_saves_attempts_as_commits_and_resets(tmp_path, monkeypatch):
    origin = tmp_path / "origin"
    origin.mkdir()
    subprocess.run(["git", "init", "-q", str(origin)], check=True)
    (origin / "main.c").write_text("int main() { return 0; }\n")
    Workspace(origin).snapshot("initial")
    monkeypatch.setattr("experiments.workspace.WORKSPACES", tmp_path / "ws")

    ws = Workspace.clone(str(origin), "task-1")
    baseline = ws.head()
    (ws.path / "main.c").write_text("int main() { return 1; }\n")
    (ws.path / "new.h").write_text("#define X 1\n")
    attempt = ws.snapshot("attempt 1: change the return code")
    assert ws.changed_files(baseline, attempt) == ["main.c", "new.h"]
    assert "+int main() { return 1; }" in ws.diff(baseline, attempt)
    ws.reset(baseline)
    assert (ws.path / "main.c").read_text() == "int main() { return 0; }\n" and not (ws.path / "new.h").exists()

def docker_running() -> bool:
    try:
        import docker
        docker.from_env().images.get("lume-sandbox:base")
        return True
    except Exception:
        return False

@pytest.mark.skipif(not docker_running(), reason="needs Docker and the lume-sandbox:base image")
def test_real_sandbox_builds_checks_and_times_a_program(tmp_path):
    from sandbox.docker_sandbox import DockerSandbox
    (tmp_path / "sum.c").write_text("#include <stdio.h>\nint main(){long s=0;for(long i=0;i<20000000;i++)s+=i;"
                                    "printf(\"%ld\\n\",s);return 0;}\n")
    spec = BenchmarkSpec(build="gcc -O1 sum.c -o sum", checks={"prints the sum": "./sum | grep -q 199999990000000"},
                         measure="./sum", repeats=3, warmup=1, timeout=60)
    with DockerSandbox(tmp_path, limits=Limits(cpus=2, memory="512m", timeout=60)) as box:
        assert box.run("curl -s https://example.com || python3 -c 'import socket; socket.create_connection((\"1.1.1.1\", 53), 3)'").ok is False
        result = run_attempt(box, spec)
    assert result["stage"] == "done" and result["checks"] == {"prints the sum": True}
    assert len(result["samples"]) == 3 and result["metric"] > 0
