from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import invoke_llm

def critic_node(state):
    print("--- CRITIC AGENT ---")
    draft_report = state.get("draft_report")
    
    system_prompt = """You are an expert peer reviewer and editor.
Review the following research report draft. 
Improve clarity, fix any structural issues, remove redundancy, and ensure coherence.
Output ONLY the refined final report. Do not add any conversational text before or after the report.
"""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=draft_report)
    ]
    
    response = invoke_llm(messages, temperature=0.1)
    return {"final_report": response.content}
