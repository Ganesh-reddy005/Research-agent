import asyncio
from utils.events import report_progress
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from utils.vectorstore import qdrant_configured, research_collection, collection_exists, get_vector_store

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

async def writer_node(state):
    print("--- WRITER AGENT: Commencing academic draft ---")
    topic = state.get("topic")
    plan = state.get("research_plan", {})
    synthesis = state.get("synthesis_report")
    sources = state.get("raw_sources", [])

    thread_id = state.get("thread_id", "default_thread")
    collection_name = research_collection(thread_id)

    vectorstore = None
    if qdrant_configured() and await asyncio.to_thread(collection_exists, collection_name):
        vectorstore = get_vector_store(collection_name)

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

    for i, section in enumerate(sections, start=1):
        title = section.get("title")
        description = section.get("description")
        await report_progress(f"Writing section {i} of {len(sections)}: {title}")

        # Evidence for this section: diverse passages (MMR) rather than several from one paper
        if vectorstore:
            results = await vectorstore.amax_marginal_relevance_search(f"{title}: {description}", k=8, fetch_k=30)
            passages = [(r.page_content, r.metadata.get("url"), r.metadata.get("title")) for r in results]
        else:
            passages = [(s.get("summary", ""), s.get("url"), s.get("title")) for s in sources[:10]]
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
3. OPTIMAL LENGTH: Be concise but rigorous. Target 150-250 words for this section. Never produce very large blocks of text.
4. TECHNICAL DEPTH: Focus on evidence and technical data over generic descriptions.
5. Do not write the section heading; it is added automatically.

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

    return {"draft_report": full_report, "current_step": "writer"}
