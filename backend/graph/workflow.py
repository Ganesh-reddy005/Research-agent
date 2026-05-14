import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

# Nodes are imported from their respective files
from agents.clarification import clarification_node
from agents.planning import planning_node
from agents.retriever import retriever_node
from agents.indexer import indexer_node
from agents.assistance import assistance_node
from agents.synthesis import synthesis_node
from agents.writer import writer_node
from agents.critic import critic_node
from agents.refinement import refinement_node
from agents.auditor import citation_auditor_node

class AgentState(TypedDict, total=False):
    topic: str
    research_mode: str 
    thread_id: str
    clarification_questions: List[Dict[str, str]]
    user_answers: Dict[str, str]
    research_brief: str
    research_plan: Dict[str, Any]
    plan_approved: bool
    plan_edits: str
    search_queries: List[str]
    raw_sources: List[Dict[str, Any]]
    assistance_summary: str
    synthesis_report: str
    draft_report: str
    critic_feedback: str
    final_report: str
    citation_audit_log: Dict[str, Any]
    current_step: str

def build_graph(checkpointer=None):
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("indexer", indexer_node)
    workflow.add_node("assistance", assistance_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("refinement", refinement_node)
    workflow.add_node("auditor", citation_auditor_node)
    
    # Define Edges
    workflow.add_edge(START, "clarification")
    workflow.add_edge("clarification", "planning")
    workflow.add_edge("planning", "retriever")
    workflow.add_edge("retriever", "indexer")
    workflow.add_edge("indexer", "assistance")
    workflow.add_edge("assistance", "synthesis")
    workflow.add_edge("synthesis", "writer")
    workflow.add_edge("writer", "critic")
    workflow.add_edge("critic", "refinement")
    workflow.add_edge("refinement", "auditor")
    workflow.add_edge("auditor", END)
    
    # Compile with interrupts for human-in-the-loop
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["clarification", "planning", "assistance"]
    )

