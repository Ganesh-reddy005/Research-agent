from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from agents.paper_length import editing_rule, editing_max_tokens

async def refinement_node(state):
    print("--- REFINEMENT AGENT: Polishing final report ---")
    draft_report = state.get("draft_report")
    critic_feedback = state.get("critic_feedback")
    topic = state.get("topic")
    
    system_prompt = f"""You are a professional academic editor specialized in IEEE Transactions.
Your goal is to perform final polishing on a research paper regarding: '{topic}'.

OUTPUT FORMAT (Markdown, exactly this structure; the system typesets it in IEEE style):
# <Paper title>
## Abstract
<one paragraph, 150-200 words>
## Index Terms
<4-6 comma-separated keywords>
## <Section title>        (one per section, in order; no numbering, it is added automatically)
### <Subsection title>    (optional)
<section text>

CITATIONS:
- Keep every citation marker such as [3] or [2], [5] exactly as it appears in the draft.
- Never remove, renumber or invent citation numbers. When you merge or shorten sentences, keep their citations.
- Do NOT write a References section; it is generated automatically from the cited sources.

POLISHING RULES:
1. No markdown bolding (**text**). Academic papers use plain text.
2. {editing_rule(state)}
3. Use formal, objective, third-person academic tone throughout.
4. Correct logical inconsistencies between sections.
5. No conversational preamble or notes. Output only the paper.
6. Never add facts, features or results that aren't in the draft.

Critique Feedback to Incorporate:
{critic_feedback}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=draft_report)
    ]
    
    # The whole paper is rewritten in one call, so allow a long output
    response = await ainvoke_llm(messages, agent_name="refinement", temperature=0.1, max_tokens=editing_max_tokens(state))
    print("--- REFINEMENT AGENT: Report finalized ---")
    return {"final_report": response.content, "current_step": "refinement"}
