"""A paper's figures and tables: charts and tables from measured results, and diagrams of what the paper
describes. Each is {"id", "kind": chart|table|diagram, "origin": measured|illustrative, "caption", "section",
and "svg" | "table" | "mermaid"}; place_figures keeps their markers valid however the text is rewritten."""
from experiments.lab import brief_text
from agents.project_context import is_project_paper, project_context
from figures.charts import experiment_figures
from figures.diagrams import plan_diagrams
from figures.placement import figure_notes, home_section, place_figures  # noqa: F401

CONTEXT_CHARS = 5000


def paper_context(state) -> str:
    """What the diagram planner reads: the topic, the synthesis, and the project or experiment if any."""
    parts = [f"Topic: {state.get('topic', '')}", f"Synthesis:\n{str(state.get('synthesis_report') or '')[:CONTEXT_CHARS]}"]
    if is_project_paper(state):
        parts.append(project_context(state)[:CONTEXT_CHARS])
    if state.get("experiment_brief"):
        parts.append(f"Experiment:\n{brief_text(state['experiment_brief'])}")
    return "\n\n".join(parts)


async def build_figures(state, sections: list[dict]) -> list[dict]:
    titles = [str(s.get("title", "")) for s in sections if s.get("title")]
    figures = experiment_figures(state)
    for figure in figures:
        figure["section"] = home_section(figure, titles)
    return figures + await plan_diagrams(paper_context(state), sections)
