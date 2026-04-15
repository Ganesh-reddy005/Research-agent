import json
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import invoke_llm

def planner_node(state):
    print("--- PLANNER AGENT ---")
    query = state.get("query")
    system_prompt = """You are an expert research planner. 
Break down the user's research query into 10 to 15 highly specific search queries that are latest (its 2026 right now).
These queries will be fed directly into web search engines and academic paper databases (like arXiv) to retrieve the latest and most relevant data.
Return the result strictly as a JSON array of strings."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    response = invoke_llm(messages)
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
        search_queries = json.loads(content)
        if not isinstance(search_queries, list):
            search_queries = [str(search_queries)]
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        search_queries = [query]
        
    return {"search_queries": search_queries}
