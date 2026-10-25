from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from agents.project_context import project_context

def project_check(state) -> str:
    project = project_context(state)
    if not project:
        return ""
    return f"""5. Claims about the authors' project that the repository analysis below doesn't support,
   especially results, metrics or features that may have been invented

{project}
"""

async def critic_node(state):
    print("--- CRITIC AGENT: Appraising draft ---")
    draft_report = state.get("draft_report")
    topic = state.get("topic")
    
    system_prompt = f"""You are a senior peer reviewer for a top-tier scientific journal.
Review the following research report draft on: '{topic}'.

Your task is to identify:
1. Weak arguments or unsubstantiated claims
2. Logical gaps in the flow
3. Areas where more technical depth or citations are needed
4. Any inconsistencies with the research brief

{project_check(state)}
Output your critique as a series of actionable, bulleted points.
Do not rewrite the paper yet; just provide the feedback."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=draft_report)
    ]
    
    response = await ainvoke_llm(messages, agent_name="critic", temperature=0.5)
    print("--- CRITIC AGENT: Feedback generated ---")
    return {"critic_feedback": response.content, "current_step": "critic"}
