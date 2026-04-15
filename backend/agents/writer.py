from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import invoke_llm

def writer_node(state):
    print("--- WRITER AGENT ---")
    query = state.get("query")
    sources = state.get("sources", [])
    
    sources_text = ""
    for i, src in enumerate(sources):
        sources_text += f"\n[{i+1}] {src.get('title')}\nURL: {src.get('url')}\nSummary: {src.get('summary')}\n"
        
    system_prompt = f"""You are an expert academic writer. 
Write a comprehensive research report on the topic: "{query}"

You must follow the IEEE-style structure:
1. Title
2. Abstract
3. Introduction
4. Methodology / Key Concepts
5. Findings / Discussion
6. Conclusion
7. References

Use the following retrieved sources to ground your content. Cite them inline like [1], [2], etc.
Do not hallucinate facts.

Sources:
{sources_text}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Please write the report now.")
    ]
    
    response = invoke_llm(messages, temperature=0.3)
    return {"draft_report": response.content}
