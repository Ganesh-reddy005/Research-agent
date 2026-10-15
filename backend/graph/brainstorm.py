from typing import Annotated, List, TypedDict
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from agents.brainstorm import BRAINSTORM_SYSTEM_PROMPT
from utils.llm import ainvoke_llm

class BrainstormState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]

async def brainstorm_node(state):
    messages = [SystemMessage(content=BRAINSTORM_SYSTEM_PROMPT)] + state["messages"]
    response = await ainvoke_llm(messages, agent_name="brainstorm")
    return {"messages": [response]}

def build_brainstorm_graph(checkpointer=None):
    """Brainstorm chats are a one-node graph so the checkpointer saves the conversation."""
    workflow = StateGraph(BrainstormState)
    workflow.add_node("brainstorm", brainstorm_node)
    workflow.add_edge(START, "brainstorm")
    workflow.add_edge("brainstorm", END)
    return workflow.compile(checkpointer=checkpointer)
