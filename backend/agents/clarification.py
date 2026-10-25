import json
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm
from agents.project_context import is_project_paper, project_context

PROJECT_PROMPT = """You are a research supervisor helping the authors of a software project write a research paper about it.
You have already analysed their repository (below). Ask 3 to 5 questions that ONLY the authors can answer
and that the repository does not already answer. Focus on:
1. The paper's purpose and audience (course report, conference, journal) and any length or format requirements
2. The authors' own contribution and what is novel compared with existing tools or work
3. Results, measurements or user studies they have that are not in the repository
4. What the paper should emphasise or leave out
5. Anything the analysis got wrong or is missing

Return the result STRICTLY as a JSON array of objects, where each object has 'id' (string) and 'question' (string)."""

async def clarification_node(state):
    print("--- CLARIFICATION AGENT ---")
    topic = state.get("topic")
    
    system_prompt = """You are an expert research consultant.
Your goal is to help the user define the scope, objectives, and domain of their research topic.
Based on the provided topic, generate 3 to 5 critical questions that will help narrow down the research.
Focus on:
1. Specificity (what EXACTLY are we researching?)
2. Objectives (what is the intended outcome?)
3. Constraints (timeframes, regions, specific technologies)
4. Hypothesis direction (what do we suspect is true?)
5. anything else essential for the research topic

Return the result STRICTLY as a JSON array of objects, where each object has 'id' (string) and 'question' (string)."""

    human = f"Topic: {topic}"
    if is_project_paper(state):
        system_prompt = PROJECT_PROMPT
        human = f"{human}\n\n{project_context(state)}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human)
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
