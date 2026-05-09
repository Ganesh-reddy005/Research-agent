from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm

async def assistance_node(state):
    print("--- ASSISTANCE AGENT ---")
    sources = state.get("raw_sources", [])
    topic = state.get("topic")
    
    if not sources:
        return {"current_step": "assistance", "assistance_summary": "No sources found to summarize."}
        
    num_sources = len(sources)
    sources_text = "\n\n".join([f"Title: {s.get('title')}\nSummary: {s.get('summary')}" for s in sources[:10]]) # limited to 10 for quick summary
    
    system_prompt = "You are a Research Assistant helping a user interact with their collected data. " \
                    "Provide a very brief 3-4 sentence executive summary of the available data " \
                    "to help the user understand what has been found before deciding to proceed with the full paper."
                    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Topic: {topic}\n\nWe found {num_sources} sources. Here is a sample:\n{sources_text}")
    ]
    
    response = await ainvoke_llm(messages, agent_name="assistance")
    
    return {
        "current_step": "assistance",
        "assistance_summary": response.content.strip()
    }
