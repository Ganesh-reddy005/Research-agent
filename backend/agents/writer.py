from utils.events import report_progress
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from evidence import section_evidence
from agents.project_context import is_project_paper, project_context
from agents.paper_length import writer_rule, evidence_size
from experiments.lab import results_context
from figures import build_figures, figure_notes, place_figures

def number_evidence(passages, sources):
    """Label each passage with its source's citation number. [n] is raw_sources[n - 1],
    the same numbering the reference list and the citation auditor use."""
    number_by_url = {s.get("url"): i + 1 for i, s in enumerate(sources)}
    blocks = []
    for text, url, title in passages:
        n = number_by_url.get(url)
        if n:  # a passage we can't attribute can't be cited
            blocks.append(f"[{n}] {title}\n{text}")
    return "\n\n".join(blocks)

def project_rules(state) -> str:
    """Extra rules when the paper writes up the authors' own repository."""
    if not is_project_paper(state):
        return ""
    return f"""
THIS IS A PROJECT PAPER: it presents the authors' own project, described below.
- Describe the project in first-person plural ("we designed", "our system").
- Claims about the project's design and implementation must come from the project's code
  passages, cited with the repository's number. Never invent features, experiments or results.
- If a section needs results the repository doesn't contain, describe how the project would be
  evaluated instead of reporting numbers.
- Use the literature passages for background, related work and comparison.

{project_context(state)}
"""

async def writer_node(state):
    print("--- WRITER AGENT: Commencing academic draft ---")
    topic = state.get("topic")
    plan = state.get("research_plan", {})
    synthesis = state.get("synthesis_report")
    sources = state.get("raw_sources", [])
    rules = project_rules(state)

    # Generate content section by section
    full_report = ""
    sections = plan.get("sections", [])

    # If no sections, fall back to default IEEE
    if not sections:
        sections = [
            {"title": "Introduction", "description": "Background and motivation"},
            {"title": "Methodology", "description": "Research approach"},
            {"title": "Findings", "description": "Key results"},
            {"title": "Conclusion", "description": "Summary and future work"}
        ]

    await report_progress("Preparing figures and tables")
    figures = await build_figures(state, sections)

    for i, section in enumerate(sections, start=1):
        title = section.get("title")
        description = section.get("description")
        await report_progress(f"Writing section {i} of {len(sections)}: {title}")

        passages = await section_evidence(state, f"{title}: {description}", k=evidence_size(state, len(sections)))
        evidence = number_evidence(passages, sources)

        system_prompt = f"""You are an elite academic writer specialized in IEEE Transactions.
Write the '{title}' section for a high-impact research paper on: '{topic}'.
Section Description: {description}

CITATIONS (most important):
- The evidence passages below are labelled with their source number, e.g. [4].
- Put the matching number in square brackets right after every claim drawn from a passage,
  e.g. "...reduces memory by 38% [4]." Combine as [2], [5] when several sources support a claim.
- Use ONLY the numbers that appear in the evidence. Never invent a citation number.
- Draw on as many different relevant sources as the evidence allows (at least 3 distinct sources when possible).
- If the evidence does not support a point, say so rather than inventing facts.

STRICT FORMATTING & LENGTH RULES:
1. NO MARKDOWN BOLDING (**text**). Use plain text for emphasis.
2. Use professional, third-person objective academic tone.
3. LENGTH: {writer_rule(state, len(sections))}
4. TECHNICAL DEPTH: Focus on evidence and technical data over generic descriptions.
5. Do not write the section heading; it is added automatically.
{rules}
{results_context(state)}
{figure_notes(figures, title)}
Synthesis Context:
{synthesis}

Evidence Passages:
{evidence or "No evidence passages were retrieved for this section."}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Write the {title} section now.")
        ]

        print(f"Drafting section: {title}...")
        response = await ainvoke_llm(messages, agent_name="writer", temperature=0.3)
        print(f"Completed {title}. ({len(response.content)} characters)")
        full_report += f"\n\n## {title}\n\n{response.content}\n"

    return {"draft_report": place_figures(full_report, figures), "figures": figures, "current_step": "writer"}
