"""The coding agent's toolbox: code lookups, the lab notebook, phase permissions and call limits."""
import asyncio
import pytest
from experiments import notebook as nb
from experiments import prior_work
from experiments.code_tools import CodeTools, MAX_READ_LINES
from experiments.toolbox import PHASE_TOOLS, ToolBudget, ToolContext, build_tools

@pytest.fixture
def code(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/kernel.c").write_text("static int dot_product(int n) {\n    return n * 2;\n}\n"
                                           + "".join(f"// line {i}\n" for i in range(300)))
    (tmp_path / "src/main.c").write_text("int main() { return dot_product(3); }\n")
    (tmp_path / "README.md").write_text("Fast dot products.\n")
    (tmp_path.parent / "secret.txt").write_text("outside the target")
    return CodeTools(tmp_path)

def test_code_lookups_answer_with_locations(code):
    assert code.find_definition("dot_product").startswith("src/kernel.c:1-3 function: static int dot_product(int n) {")
    assert "src/main.c:1" in code.find_references("dot_product")
    assert "Similar names: dot_product" in code.find_definition("dot")
    assert "L1-3 function dot_product" in code.outline("src/kernel.c")
    assert "src/kernel.c" in code.repo_map(focus="dot")

def test_read_file_is_numbered_capped_and_stays_inside_the_target(code):
    text = code.read_file("src/kernel.c", start=2, end=3)
    assert text.splitlines()[1:] == ["2:     return n * 2;", "3: }"]
    assert len(code.read_file("src/kernel.c").splitlines()) == MAX_READ_LINES + 1  # header + capped lines
    assert code.read_file("../secret.txt").startswith("No such file")
    assert code.read_file("/etc/passwd").startswith("No such file")

def test_grep_searches_text_files_and_rejects_bad_patterns(code):
    assert "README.md:1: Fast dot products." in code.grep("dot products")
    assert "README.md" not in code.grep("dot", glob="*.c")
    assert code.grep("(").startswith("Invalid pattern")
    assert "more matches" in code.grep("line")

def test_grep_searches_files_even_when_stdin_is_a_pipe(code, monkeypatch):
    # ripgrep searches stdin instead of files when given no path and stdin isn't a terminal
    import subprocess
    real_run = subprocess.run
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: real_run(*a, **{**k, "stdin": k.get("stdin", subprocess.PIPE)}))
    assert "src/main.c:1:" in code.grep("dot_product")

def test_verdicts_treat_noise_and_failed_checks_honestly():
    assert nb.verdict(None, {}, 10, "maximize") == nb.CRASHED
    assert nb.verdict(99, {"tests": False}, 10, "maximize") == nb.FAILED_CHECKS  # a great number with a broken check
    assert nb.verdict(10.4, {"tests": True}, 10, "maximize", spread=0.5) == nb.NO_GAIN  # within run-to-run noise
    assert nb.verdict(11, {"tests": True}, 10, "maximize", spread=0.5) == nb.IMPROVED
    assert nb.verdict(11, {"tests": True}, 10, "minimize", spread=0.5) == nb.WORSE
    assert nb.verdict(5, {}, None, "minimize") == nb.BASELINE  # the first result sets the bar
    assert nb.verdict(None, {"tests": False}, 10, "minimize") == nb.FAILED_CHECKS  # stopped at the check, not a crash

def test_notebook_tracks_the_best_valid_attempt_and_spots_repeats():
    book = []
    book.append(nb.record(book, "maximize", "baseline build", "nothing", {"tests": True}, 100.0, spread=1.0))
    book.append(nb.record(book, "maximize", "unroll the inner dot product loop", "kernel.c", {"tests": False}, 140.0,
                          lesson="unrolling broke odd lengths"))
    book.append(nb.record(book, "maximize", "use 4 threads instead of 8", "config", {"tests": True}, 110.0, spread=1.0))
    assert [a["verdict"] for a in book] == [nb.BASELINE, nb.FAILED_CHECKS, nb.IMPROVED]
    assert nb.best_attempt(book, "maximize")["n"] == 3  # 140 failed a check, so it doesn't count
    assert nb.already_tried(book, "Unroll the inner dot-product loop")["n"] == 2
    assert nb.already_tried(book, "vectorise the reduction with NEON") is None
    text = nb.render(book, "maximize")
    assert "#2 [failed checks]" in text and "failed: tests" in text and "Best so far: #3 (110)" in text

def ctx(code):
    return ToolContext(code=code, target="https://github.com/owner/repo", goal="maximize")

def test_each_phase_gets_only_its_tools(code):
    from experiments.edit_tools import EditTools
    from experiments.harness import BenchmarkSpec
    for phase, allowed in PHASE_TOOLS.items():
        context = ctx(code)
        if phase == "code":
            with pytest.raises(ValueError):
                build_tools(phase, context)  # editing needs a sandbox and the approved benchmark
            context.edits = EditTools(code, box=None, spec=BenchmarkSpec(measure="m"))
        assert [t.name for t in build_tools(phase, context)] == list(allowed)
    assert "ask_user" not in PHASE_TOOLS["code"] and "search_literature" not in PHASE_TOOLS["understand"]
    with pytest.raises(ValueError):
        build_tools("deploy", ctx(code))

def test_tools_stop_working_past_their_limit(code):
    budget = ToolBudget(limits={"find_definition": 2})
    tool = next(t for t in build_tools("understand", ctx(code), budget) if t.name == "find_definition")
    assert tool.invoke({"name": "dot_product"}).startswith("src/kernel.c")
    tool.invoke({"name": "dot_product"})
    assert tool.invoke({"name": "dot_product"}).startswith("Limit reached: find_definition can be used 2 times")

def test_already_tried_tool_reads_the_notebook(code):
    context = ctx(code)
    context.notebook.append(nb.record([], "maximize", "unroll the dot product loop", "c", {"t": True}, 1.0, lesson="no gain"))
    tool = next(t for t in build_tools("plan", context) if t.name == "check_already_tried")
    assert tool.invoke({"idea": "unroll dot product loop"}).startswith("Already tried as #1")

def test_project_history_lists_issues_and_merged_prs(monkeypatch):
    class Response:
        status_code = 200
        def json(self):
            return {"items": [{"number": 7, "state": "closed", "title": "Unroll dot loop", "html_url": "u7",
                               "body": "Tried it: slower on ARM.", "pull_request": {"merged_at": None}},
                              {"number": 9, "state": "closed", "title": "NEON dot", "html_url": "u9",
                               "body": "Merged.", "pull_request": {"merged_at": "2026-01-01"}}]}
    class Client:
        def __init__(self, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, url, params): self.params = params; return Response()
    monkeypatch.setattr(prior_work.httpx, "AsyncClient", Client)
    text = asyncio.run(prior_work.search_project_history("https://github.com/owner/repo", "dot unroll"))
    assert "PR #7 [closed] Unroll dot loop" in text and "PR #9 [closed merged] NEON dot" in text
    assert asyncio.run(prior_work.search_project_history("a local folder", "x")).startswith("The target isn't a GitHub")

def test_literature_search_reuses_the_retriever_providers(monkeypatch):
    async def fake_run_need(need, user_id, per_provider):
        assert need == {"query": "loop unrolling", "kind": "papers"} and user_id is None
        return [{"title": "Unrolling Loops", "year": 2001, "url": "https://x", "summary": "s " * 200}]
    monkeypatch.setattr(prior_work, "run_need", fake_run_need)
    text = asyncio.run(prior_work.search_literature("loop unrolling", kind="nonsense"))  # unknown kinds -> papers
    assert text.startswith("- Unrolling Loops (2001) https://x") and text.endswith("…")

def test_edit_tools_change_code_but_never_protected_files(code):
    from experiments.edit_tools import EditTools
    from experiments.harness import BenchmarkSpec
    edits = EditTools(code, box=None, spec=BenchmarkSpec(measure="m", protected=("tests/", "src/main.c")))
    assert edits.edit_file("src/kernel.c", "return n * 2;", "return n << 1;") == "Edited src/kernel.c."
    assert "return n << 1;" in (code.root / "src/kernel.c").read_text()
    assert "appears 0 times" in edits.edit_file("src/kernel.c", "return n * 2;", "x")
    assert edits.edit_file("src/main.c", "int", "long").startswith("src/main.c is protected")
    assert edits.write_file("tests/test_new.py", "assert True").startswith("tests/test_new.py is protected")
    assert edits.write_file("../escape.c", "x").endswith("outside the target.")
    assert edits.write_file(".git/config", "x").endswith("outside the target.")
    assert edits.write_file("src/fast.c", "static int fast_dot(int n) { return n; }\n").startswith("Wrote src/fast.c")
    assert code.find_definition("fast_dot").startswith("src/fast.c:1")  # the code graph sees the new file
