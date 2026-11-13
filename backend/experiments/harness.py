"""Scoring an attempt: build, run the checks, then measure, cheapest first. A broken build never
pays for a benchmark, and one quick measurement comes before the full repeats.

The spec is fixed when the user approves the plan; the agent can't change how it is graded. Timings
use hyperfine (warm-up, repeats, mean and spread); other metrics are read from the measure command's
output, as a JSON key or a regular expression."""
import fnmatch
import json
import re
import shlex
import statistics
from dataclasses import asdict, dataclass, field

TIME, JSON_PREFIX, REGEX_PREFIX = "time", "json:", "regex:"
HYPERFINE_OUT = "/tmp/lume-hyperfine.json"


@dataclass(frozen=True)
class BenchmarkSpec:
    measure: str  # the command whose time, or printed number, is the metric
    read: str = TIME  # "time", "json:<dotted.key>" or "regex:<pattern with one group>"
    build: str = ""
    checks: dict = field(default_factory=dict)  # name -> command that must exit 0
    repeats: int = 5
    warmup: int = 1
    timeout: int = 600  # seconds per command
    protected: tuple = ()  # globs of files no attempt may change: tests, benchmark inputs, the checks themselves

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkSpec":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "protected" in fields:
            fields["protected"] = tuple(fields["protected"] or ())
        return cls(**fields)

    def is_protected(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(path, f"{glob.rstrip('/')}/*") for glob in self.protected)


def read_number(text: str, read: str) -> float | None:
    """The metric in a command's output, or None if it isn't there."""
    try:
        if read.startswith(JSON_PREFIX):
            value = json.loads(text.strip().splitlines()[-1])  # the last line holds the JSON
            for key in read[len(JSON_PREFIX):].split("."):
                value = value[int(key)] if isinstance(value, list) else value[key]
            return float(value)
        if read.startswith(REGEX_PREFIX):
            match = re.search(read[len(REGEX_PREFIX):], text)
            return float(match.group(1)) if match else None
    except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError, re.error):
        return None
    return None


def _failed(result, stage: str, error: str, log: str) -> dict:
    return {**result, "stage": stage, "error": error, "log": log}


def _measure(box, spec: BenchmarkSpec, runs: int, warmup: int) -> tuple[list[float], str | None, str]:
    """(samples, error, log tail)."""
    if spec.read == TIME:
        command = (f"hyperfine --style none --warmup {warmup} --runs {max(runs, 2)} "
                   f"--export-json {HYPERFINE_OUT} {shlex.quote(spec.measure)} && cat {HYPERFINE_OUT}")
        out = box.run(command, timeout=spec.timeout * (runs + warmup + 1))
        if not out.ok:
            return [], "the measure command failed or timed out", out.tail()
        times = json.loads(out.stdout[out.stdout.index("{"):])["results"][0]["times"]
        return times[:runs], None, ""
    samples = []
    for i in range(warmup + runs):
        out = box.run(spec.measure, timeout=spec.timeout)
        value = read_number(out.stdout, spec.read) if out.ok else None
        if value is None:
            return samples, f"no {spec.read} value in the measure output" if out.ok else "the measure command failed", out.tail()
        if i >= warmup:
            samples.append(value)
    return samples, None, ""


def run_attempt(box, spec: BenchmarkSpec, quick: bool = False, changed: list[str] | None = None) -> dict:
    """Build, checks, one quick measurement, then (unless quick) the full repeats. Stops at the first
    failure. changed: the attempt's changed files; touching a protected one fails it before anything runs.
    Returns the stage reached, check results, metric (mean), spread (stdev) and samples."""
    result = {"stage": "build", "checks": {}, "metric": None, "spread": None, "samples": [], "error": "", "log": ""}
    touched = [path for path in changed or [] if spec.is_protected(path)]
    if touched:
        result["checks"]["protected files unchanged"] = False
        return _failed(result, "checks", "changed protected files", ", ".join(touched))
    if spec.build:
        out = box.run(spec.build, timeout=spec.timeout)
        result["build_seconds"] = out.seconds
        if not out.ok:
            return _failed(result, "build", "timed out" if out.timed_out else "the build failed", out.tail())
    result["stage"] = "checks"
    for name, command in spec.checks.items():
        out = box.run(command, timeout=spec.timeout)
        result["checks"][name] = out.ok
        if not out.ok:
            return _failed(result, "checks", f"check failed: {name}", out.tail())
    result["stage"] = "quick measure"
    samples, error, log = _measure(box, spec, runs=1, warmup=0)
    if error or quick:
        return _failed(result, "quick measure", error, log) if error else {**result, "metric": samples[0], "spread": 0.0, "samples": samples}
    result["stage"] = "measure"
    samples, error, log = _measure(box, spec, runs=spec.repeats, warmup=spec.warmup)
    if error:
        return _failed(result, "measure", error, log)
    spread = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return {**result, "stage": "done", "metric": statistics.mean(samples), "spread": spread, "samples": samples}
