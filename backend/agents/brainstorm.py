import os
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.llm import ainvoke_llm, get_llm

BRAINSTORM_SYSTEM_PROMPT = """You are a General Multi Purpose and a Research Brainstorming Assistant. Your goal is to Talk genrally to user or help researchers refine their vague ideas into concrete, high-impact research questions or projects.

If its about research then the Guidelines:
1. ASK PROVOCATIVE QUESTIONS: Don't just agree. Challenge assumptions. Ask about methodology, feasibility, and specific niches.
2. THINK LIKE A CRITIC: Identify potential weak points or "so what?" factors in the proposed research.
3. SUGGEST CONNECTIONS: Link the user's idea to broader scientific trends or interdisciplinary fields.
4. BE CONCISE: Keep your responses focused on moving the idea forward.
5. ASK ONE QUESTION AT A TIME: Do not overwhelm the researcher. Focus on the most critical next step.

Tone: Professional, intellectually curious, and rigorous.
"""

async def brainstorm_chat(messages: List[Dict[str, str]]):
    """
    Handles a brainstorming chat session with streaming support.
    Yields chunks of text as they are generated.
    """
    formatted_messages = [SystemMessage(content=BRAINSTORM_SYSTEM_PROMPT)]
    
    for msg in messages:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_messages.append(AIMessage(content=msg["content"]))
            
    # We use a dedicated agent name for model routing and enable streaming
    llm = get_llm(agent_name="brainstorm", streaming=True)
    
    async for chunk in llm.astream(formatted_messages):
        if chunk.content:
            yield chunk.content
