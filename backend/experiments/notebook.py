"""The lab notebook: every attempt, what it changed, whether the checks held, what it scored and what
was learned. The agent reads it before planning, so it never pays twice for the same failed idea, and
the paper is written from it, failures included.

An attempt is a plain dict (it lives in the graph state):
{"n", "hypothesis", "change", "checks": {name: passed}, "metric", "spread", "verdict", "lesson", "cost_usd"}"""
import re

BASELINE, IMPROVED, NO_GAIN, WORSE = "baseline", "improved", "no gain", "worse"
BASELINE_NAME = "baseline: the unmodified code"
FAILED_CHECKS, CRASHED = "failed checks", "crashed"
WORKS = "works"  # a build step that runs and passes its checks (no baseline to compare with)
SIMILAR = 0.6  # word overlap above which a new hypothesis counts as already tried
_WORDS = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "to", "of", "and", "or", "in", "on", "for", "with", "by", "use", "try", "using", "instead"}


def verdict(metric, checks: dict, best, goal: str, spread: float = 0.0) -> str:
    """How an attempt went against the best result so far. A gain smaller than the run-to-run spread
    is noise, not an improvement; and no number counts if a check failed."""
    if not all(checks.values()):
        return FAILED_CHECKS  # checked first: a failed check stops the run before anything is measured
    if metric is None:
        return CRASHED
    if best is None:
        return BASELINE  # the first measured result sets the bar
    gain = metric - best if goal == "maximize" else best - metric
    if gain > spread:
        return IMPROVED
    return WORSE if gain < -spread else NO_GAIN


def best_attempt(notebook: list[dict], goal: str) -> dict | None:
    """The best attempt that passed every check."""
    valid = [a for a in notebook if a.get("metric") is not None and all(a.get("checks", {}).values())]
    if not valid:
        return None
    return (max if goal == "maximize" else min)(valid, key=lambda a: a["metric"])


def record(notebook: list[dict], goal: str, hypothesis: str, change: str, checks: dict, metric,
           spread: float = 0.0, lesson: str = "", cost_usd: float = 0.0, results: dict | None = None) -> dict:
    """A new attempt with its verdict (not yet added to the notebook). With results (a build step's
    table), there is no baseline: the step works, or it failed its checks or didn't run."""
    best = best_attempt(notebook, goal)
    if results is not None:
        outcome = FAILED_CHECKS if not all(checks.values()) else WORKS
    elif not all(checks.values()) or metric is not None:
        outcome = verdict(metric, checks, best["metric"] if best else None, goal, spread)
    else:
        outcome = CRASHED
    return {"n": len(notebook) + 1, "hypothesis": hypothesis, "change": change, "checks": dict(checks),
            "metric": metric, "spread": spread, "lesson": lesson, "cost_usd": round(cost_usd, 4),
            "results": results, "verdict": outcome}


def _keywords(text: str) -> set[str]:
    return {w for w in _WORDS.findall(text.lower()) if w not in _STOP}


def already_tried(notebook: list[dict], hypothesis: str) -> dict | None:
    """An earlier attempt with nearly the same idea, so the agent is warned before repeating it."""
    words = _keywords(hypothesis)
    for attempt in notebook:
        earlier = _keywords(attempt["hypothesis"])
        if words and earlier and len(words & earlier) / len(words | earlier) >= SIMILAR:
            return attempt
    return None


def render(notebook: list[dict], goal: str) -> str:
    """The notebook as the agent reads it: one line per attempt, then the best so far."""
    if not notebook:
        return "No attempts yet."
    lines = []
    for a in notebook:
        failed = [name for name, ok in a["checks"].items() if not ok]
        if a.get("results"):
            result = "; ".join(f"{k} {v['mean']:.4g}" + (f" ±{v['spread']:.2g}" if v["spread"] else "") for k, v in a["results"].items())
        elif a["metric"] is not None:
            result = f"{a['metric']:.4g}" + (f" ±{a['spread']:.2g}" if a.get("spread") else "")
        else:
            result = "no result"
        lines.append(f"#{a['n']} [{a['verdict']}] {a['hypothesis']} -> {result}"
                     + (f"; failed: {', '.join(failed)}" if failed else "") + (f". Lesson: {a['lesson']}" if a.get("lesson") else ""))
    working = [a for a in notebook if a["verdict"] == WORKS]
    if any(a.get("results") is not None for a in notebook):  # building from scratch: no baseline, no "best"
        lines.append(f"Latest working step: #{working[-1]['n']}" if working else "No step has passed its checks yet.")
        return "\n".join(lines)
    best = best_attempt(notebook, goal)
    lines.append(f"Best so far: #{best['n']} ({best['metric']:.4g})" if best else "No attempt has passed every check yet.")
    return "\n".join(lines)
