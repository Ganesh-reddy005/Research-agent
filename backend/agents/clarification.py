import json
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm

async def clarification_node(state):
    print("--- CLARIFICATION AGENT ---")
    topic = state.get("topic")
    
    system_prompt = """You are an expert research consultant.
Your goal is to help the user define the scope, objectives, and domain of their research topic.
Based on the provided topic, generate 5 to 10 critical questions that will help narrow down the research.
Focus on:
1. Specificity (what EXACTLY are we researching?)
2. Objectives (what is the intended outcome?)
3. Constraints (timeframes, regions, specific technologies)
4. Hypothesis direction (what do we suspect is true?)

Return the result STRICTLY as a JSON array of objects, where each object has 'id' (string) and 'question' (string)."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Topic: {topic}")
    ]
    
    response = await ainvoke_llm(messages, agent_name="clarification")
    
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        questions = json.loads(content)
        if not isinstance(questions, list):
            questions = [{"id": "1", "question": str(questions)}]
    except Exception as e:
        print(f"Error parsing clarification questions: {e}")
        questions = [
            {"id": "1", "question": f"Could you provide more details about the scope of '{topic}'?"},
            {"id": "2", "question": "What specifically would you like to focus on?"}
        ]

    return {"clarification_questions": questions, "current_step": "clarification"}
