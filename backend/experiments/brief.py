"""The experiment brief: what the coding agent should improve, how success is measured, and what it
must not break or touch. Drafted from the research so far; the user edits and approves it before
anything runs.

Nothing here is specific to one project or benchmark: the target, metric and checks all come from
the user's research and edits."""
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from agents.project_context import project_context
from utils.llm import ainvoke_llm

GOALS = {"maximize", "minimize"}
DEFAULT_ATTEMPTS = 5
MAX_ATTEMPTS = 20  # a safety net: the user decides after every attempt anyway
MAX_ITEMS = 12  # per list field
SOURCES_SHOWN = 12

PROMPT = """You draft the brief for a coding agent that will run experiments for this research. The agent will
write and run code, measure the result, compare it with the baseline, and report to the user after every attempt.

Write what the agent needs to know before it starts:
- objective: one or two sentences: what to improve or test, on which system.
- target: the repository to experiment on, only if the research or the user names one (its URL); otherwise
  leave it empty, and Lume will look for existing code to start from, or write it from scratch.
- metric: the single number the objective asks to improve (e.g. if the objective is speed, a time or a
  throughput, not an accuracy). name, goal ("maximize" or "minimize") and measured_by (the tool, command or
  procedure that produces it, if the research names one). Quality metrics are measured on held-out data, never
  on the data used for training or tuning.
- baseline: what the result is compared with: the unmodified system, or a published result. Quote a number only
  if a source below states it; never invent one.
- must_hold: checks every attempt must still pass so a better number is a real improvement: correctness tests,
  and any quality that must not drop while the metric improves, with a tolerance (e.g. "held-out accuracy within
  0.1 points of the baseline"), and the same data or configuration as the baseline.
- off_limits: what the agent must not change, because changing it would make the comparison unfair.
- open_questions: what you could not determine and the user must answer before the agent starts.
Be specific to this research; leave a field empty rather than guess.
Return STRICTLY a JSON object:
{"objective": "", "target": "", "metric": {"name": "", "goal": "maximize", "measured_by": ""}, "baseline": "",
 "must_hold": [], "off_limits": [], "open_questions": []}"""


def _text(value) -> str:
    return " ".join(str(value or "").split())


def _items(value) -> list[str]:
    items = value if isinstance(value, list) else [value] if value else []
    return [t for t in (_text(i) for i in items) if t][:MAX_ITEMS]


def _attempts(value) -> int:
    try:
        return min(max(int(value), 1), MAX_ATTEMPTS)
    except (TypeError, ValueError):
        return DEFAULT_ATTEMPTS


def normalise_brief(raw, default_target: str = "") -> dict:
    """Every field present and of the right type, whatever the model or the user sent."""
    raw = raw if isinstance(raw, dict) else {}
    metric = raw.get("metric") if isinstance(raw.get("metric"), dict) else {}
    goal = _text(metric.get("goal")).lower()
    return {
        "objective": _text(raw.get("objective")),
        "target": _text(raw.get("target")) or default_target,
        "metric": {"name": _text(metric.get("name")), "goal": goal if goal in GOALS else "maximize",
                   "measured_by": _text(metric.get("measured_by"))},
        "baseline": _text(raw.get("baseline")),
        "must_hold": _items(raw.get("must_hold")),
        "off_limits": _items(raw.get("off_limits")),
        "open_questions": _items(raw.get("open_questions")),
        "notes": _items(raw.get("notes")),  # the user's answers and anything else the agent should know
        "attempt_limit": _attempts(raw.get("attempt_limit", DEFAULT_ATTEMPTS)),
    }


def missing_fields(brief: dict) -> list[str]:
    """What must be filled in before the agent can start; empty when the brief is ready."""
    # No target is fine: Lume looks for existing code to start from, or writes it from scratch
    missing = [label for label, value in [("objective", brief["objective"]), ("metric", brief["metric"]["name"])] if not value]
    return missing + (["answers to the open questions"] if brief["open_questions"] else [])


def json_object(content: str) -> dict:
    """The largest JSON object in a model's answer, wherever it sits: answers wrap it in prose or code
    fences, and may mention other braces (code, examples) before or after it."""
    decoder, best = json.JSONDecoder(), {}
    for start in (m.start() for m in re.finditer(r"\{", content or "")):
        try:
            data, end = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and end - start > len(json.dumps(best)):
            best = data
    return best


def _context(state) -> str:
    plan = state.get("research_plan") or {}
    sections = "\n".join(f"- {s.get('title')}: {s.get('description')}" for s in plan.get("sections", []))
    sources = "\n".join(f"- {s.get('title')}: {_text(s.get('summary'))[:200]}"
                        for s in (state.get("raw_sources") or [])[:SOURCES_SHOWN])
    parts = [f"Topic: {state.get('topic')}", f"Research brief: {state.get('research_brief', '')}",
             f"Objective: {plan.get('objective', '')}", f"Plan sections:\n{sections}",
             project_context(state), f"Sources found:\n{sources}"]
    return "\n\n".join(p for p in parts if p.strip())


async def draft_brief(state) -> dict:
    """A first brief from the research so far, for the user to edit; a mostly empty one if the model's
    answer can't be read, so the user can still fill it in."""
    messages = [SystemMessage(content=PROMPT), HumanMessage(content=_context(state))]
    response = await ainvoke_llm(messages, agent_name="experiment_brief")
    return normalise_brief(json_object(response.content), default_target=state.get("repo_url", ""))
