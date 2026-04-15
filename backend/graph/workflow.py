from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

from agents.planner import planner_node
from agents.retriever import retriever_node
from agents.writer import writer_node
from agents.critic import critic_node

class AgentState(TypedDict, total=False):
    query: str
    search_queries: List[str]
    sources: List[Dict[str, Any]]
    draft_report: str
    final_report: str

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("critic", critic_node)
    
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "writer")
    workflow.add_edge("writer", "critic")
    workflow.add_edge("critic", END)
    
    return workflow.compile()
