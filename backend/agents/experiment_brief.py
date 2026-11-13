"""Graph node: draft the experiment brief the user reviews before the coding agent starts."""
from utils.events import report_progress
from experiments.brief import draft_brief


async def experiment_brief_node(state):
    print("--- EXPERIMENT BRIEF ---")
    await report_progress("Working out what to measure and what must not break")
    return {"experiment_brief": await draft_brief(state), "current_step": "experiment_brief"}
