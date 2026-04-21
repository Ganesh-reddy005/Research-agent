from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm

async def refinement_node(state):
    print("--- REFINEMENT AGENT: Polishing final report ---")
    draft_report = state.get("draft_report")
    critic_feedback = state.get("critic_feedback")
    topic = state.get("topic")
    
    system_prompt = f"""You are a professional academic editor specialized in IEEE Transactions.
Your goal is to perform final polishing on a research paper regarding: '{topic}'.

CRITICAL POLISHING RULES:
1. REMOVE ALL MARKDOWN BOLDING (**text**). Academic papers use plain text.
2. OPTIMIZE FOR LENGTH: Prune redundant sentences, 'fluff', or overly long explanations. Aim for a high-density, concise academic style.
3. Ensure a strict IEEE hierarchy (Title, Abstract, Introduction, Section I, II... Conclusion, References).
4. Use formal, objective, third-person academic tone throughout.
5. Correct any logical inconsistencies between sections.
6. Maintain perfectly formatted citations [1], [2].
7. DO NOT include any conversational preamble or metadata description. 
8. Output ONLY the raw final paper text suitable for professional publication.
9.keep each section max 300-400 words only keeping it concise and to the point.

Critique Feedback to Incorporate:
{critic_feedback}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=draft_report)
    ]
    
    response = await ainvoke_llm(messages, agent_name="refinement", temperature=0.1)
    print("--- REFINEMENT AGENT: Report finalized ---")
    return {"final_report": response.content, "current_step": "refinement"}
