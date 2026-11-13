"""How the coding agent changes and tries code during an attempt: exact edits, new files, commands in
the attempt's sandbox (no network), and a quick check with the approved benchmark.

Protected files (tests, benchmark inputs) are refused here; the grader also checks the final diff,
since a shell command could still change them."""
from experiments.code_tools import CodeTools
from experiments.harness import BenchmarkSpec, run_attempt

MAX_WRITE_BYTES = 200_000
COMMAND_TIMEOUT = 300  # seconds; full benchmarks are the grader's job
OUTPUT_CHARS = 3000


class EditTools:
    def __init__(self, code: CodeTools, box, spec: BenchmarkSpec):
        self.code, self.box, self.spec = code, box, spec

    def _target(self, path: str):
        """(file, refusal): the file inside the target, or why it may not be changed."""
        resolved = (self.code.root / path).resolve()
        if not resolved.is_relative_to(self.code.root) or ".git" in resolved.relative_to(self.code.root).parts:
            return None, f"{path} is outside the target."
        if self.spec.is_protected(resolved.relative_to(self.code.root).as_posix()):
            return None, f"{path} is protected: tests and benchmark files can't be changed, so the result stays honest."
        return resolved, None

    def edit_file(self, path: str, old: str, new: str) -> str:
        """Replace one exact occurrence of old with new."""
        target, refusal = self._target(path)
        if refusal:
            return refusal
        if not target.is_file():
            return f"No such file: {path}. Use write_file to create one."
        text = target.read_text(errors="replace")
        count = text.count(old) if old else 0
        if count != 1:
            return (f"old must appear exactly once in {path}; it appears {count} times. "
                    "Read the lines again and include more surrounding context.")
        target.write_text(text.replace(old, new, 1))
        self.code.graph.update_file(target.relative_to(self.code.root).as_posix())
        return f"Edited {path}."

    def write_file(self, path: str, content: str) -> str:
        """Create a file, or replace one entirely."""
        target, refusal = self._target(path)
        if refusal:
            return refusal
        if len(content.encode()) > MAX_WRITE_BYTES:
            return f"Too large: files are limited to {MAX_WRITE_BYTES // 1000} KB."
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        self.code.graph.update_file(target.relative_to(self.code.root).as_posix())
        return f"Wrote {path} ({len(content.splitlines())} lines)."

    def run_command(self, command: str) -> str:
        """A shell command in the attempt's sandbox (no network), e.g. compile or run one test."""
        result = self.box.run(command, timeout=min(self.spec.timeout, COMMAND_TIMEOUT))
        status = "timed out" if result.timed_out else f"exit {result.exit_code}"
        return f"{status} after {result.seconds}s\n{result.tail(OUTPUT_CHARS)}"

    def quick_check(self) -> str:
        """Build, checks and one measurement with the approved benchmark: is this attempt worth grading?"""
        result = run_attempt(self.box, self.spec, quick=True)
        if result["error"]:
            return f"Failed at {result['stage']}: {result['error']}\n{result['log'][-OUTPUT_CHARS:]}"
        if result.get("results") is not None:  # a results table (code written from scratch)
            table = "; ".join(f"{name} {v['mean']:.4g}" for name, v in result["results"].items()) or "no results yet"
            return f"Builds, checks pass, one run of the measure printed: {table}. The grader will run the full repeats."
        return f"Builds, checks pass, one measurement: {result['metric']:.4g}. The grader will run the full repeats."
