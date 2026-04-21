import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm

async def planning_node(state):
    print("--- PLANNING AGENT ---")
    topic = state.get("topic")
    questions = state.get("clarification_questions", [])
    answers = state.get("user_answers", {})
    
    # Construct a brief based on the Q&A
    qa_pairs = ""
    for q in questions:
        q_id = q.get("id")
        answer = answers.get(q_id, "No answer provided.")
        qa_pairs += f"Q: {q.get('question')}\nA: {answer}\n\n"

    system_prompt = """You are a senior research architect.
Create a comprehensive Research Brief and a detailed Research Plan based on the topic and user answers.

STRICT JSON FORMAT REQUIRED:
{
  "research_brief": "A 2-3 paragraph overview of the research goals and methodology.",
  "research_plan": {
    "objective": "Clear statement of what this research will achieve.",
    "sections": [
      {
        "title": "Section Title",
        "description": "What this section covers.",
        "questions": ["Specific question 1", "Specific question 2"]
      }
    ],
    "expected_outcome": "Description of the final value of this report."
  }
}

PLANNING CONSTRAINTS:
1. Target exactly 5-6 sections for the paper (Introduction, 3-4 body sections, Conclusion).
2. Avoid redundant or overlapping sections.
3. Each section must have a distinct, non-trivial research focus.

Return ONLY the JSON object. Do not include any other text."""

    input_text = f"Topic: {topic}\n\nUser Context:\n{qa_pairs}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=input_text)
    ]
    
    response = await ainvoke_llm(messages, agent_name="planning")
    
    content = response.content.strip()
    research_brief = f"Research on {topic} based on user inputs."
    research_plan = {
        "objective": f"Explore {topic}",
        "sections": [
            {"title": "Introduction", "description": "Overview of the topic.", "questions": ["What is the current state?"]},
            {"title": "Analysis", "description": "Deep dive into data.", "questions": ["What do the sources say?"]},
            {"title": "Conclusion", "description": "Final findings.", "questions": ["What are the implications?"]}
        ],
        "expected_outcome": "A comprehensive analysis report."
    }

    try:
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            plan_data = json.loads(json_str)
            if "research_brief" in plan_data: research_brief = plan_data["research_brief"]
            if "research_plan" in plan_data: research_plan = plan_data["research_plan"]
        else:
            print("No JSON found in planner output, using fallback.")
    except Exception as e:
        print(f"Error parsing research plan: {e}. Output was: {content[:200]}...")

    return {
        "research_brief": research_brief, 
        "research_plan": research_plan,
        "current_step": "planning"
    }
