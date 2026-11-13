import os
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
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
from agents.repo_ingest import repo_ingest_node
from agents.experiment_brief import experiment_brief_node
from agents.experiment_setup import understand_node, plan_node, setup_node
from agents.experiment_loop import attempt_node, reflect_node, route_after_plan, route_after_report, route_after_setup
from agents.experiment_start import scout_node, design_node, route_after_launch, route_after_scout
from repo.github import is_transient

class AgentState(TypedDict, total=False):
    topic: str
    research_mode: str 
    target_pages: int  # requested paper length in IEEE pages; unset means the default short paper
    thread_id: str
    user_id: str
    clarification_questions: List[Dict[str, str]]
    user_answers: Dict[str, str]
    research_brief: str
    research_plan: Dict[str, Any]
    plan_approved: bool
    plan_edits: str
    search_queries: List[str]
    search_plan: List[Dict[str, Any]]  # each need: section, need, kind, query, sources kept
    raw_sources: List[Dict[str, Any]]
    indexed_count: int
    assistance_summary: str
    synthesis_report: str
    draft_report: str
    critic_feedback: str
    final_report: str
    citation_audit_log: Dict[str, Any]
    current_step: str
    # Project paper: the repository the paper is about
    repo_url: str
    project_notes: str
    project_profile: Dict[str, Any]
    # Experiments: chosen at the review pause instead of writing the draft straight away
    wants_experiments: bool
    experiment_brief: Dict[str, Any]
    launch_experiments: bool  # the user launched the coding agent from the brief
    lab: Dict[str, Any]  # the coding agent's working state: workspace, plan, benchmark, image, report
    notebook: List[Dict[str, Any]]  # every attempt, baseline first
    figures: List[Dict[str, Any]]  # the paper's charts, tables and diagrams (see figures/)
    last_attempt: Dict[str, Any]
    experiment_decision: Dict[str, Any]  # after each report: continue, change plan (with a direction) or stop

def route_start(state) -> Literal["repo_ingest", "clarification"]:
    """A project paper reads its repository before asking questions."""
    return "repo_ingest" if state.get("repo_url") else "clarification"

def route_after_brief(state) -> Literal["exp_understand", "exp_scout", "synthesis"]:
    return route_after_launch(state) if state.get("launch_experiments") else "synthesis"

def route_after_review(state) -> Literal["experiment_brief", "synthesis"]:
    """After the sources are reviewed: write the draft, or first plan experiments for the coding agent."""
    return "experiment_brief" if state.get("wants_experiments") else "synthesis"

def build_graph(checkpointer=None):
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("repo_ingest", repo_ingest_node,
                      retry_policy=RetryPolicy(max_attempts=3, retry_on=is_transient))
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
    workflow.add_node("experiment_brief", experiment_brief_node)
    workflow.add_node("exp_scout", scout_node)
    workflow.add_node("exp_design", design_node)
    workflow.add_node("exp_understand", understand_node)
    workflow.add_node("exp_plan", plan_node)
    workflow.add_node("exp_setup", setup_node)
    workflow.add_node("exp_attempt", attempt_node)
    workflow.add_node("exp_reflect", reflect_node)
    
    # Define Edges
    workflow.add_conditional_edges(START, route_start, ["repo_ingest", "clarification"])
    workflow.add_edge("repo_ingest", "clarification")
    workflow.add_edge("clarification", "planning")
    workflow.add_edge("planning", "retriever")
    workflow.add_edge("retriever", "indexer")
    workflow.add_edge("indexer", "assistance")
    workflow.add_conditional_edges("assistance", route_after_review, ["experiment_brief", "synthesis"])
    # The coding agent: understand -> plan (approved) -> setup + baseline -> report (decided) -> attempt -> report ...
    # No repository named: find one to start from (the user confirms), or design the code from scratch
    workflow.add_conditional_edges("experiment_brief", route_after_brief, ["exp_understand", "exp_scout", "synthesis"])
    workflow.add_conditional_edges("exp_scout", route_after_scout, ["exp_understand", "exp_design"])
    workflow.add_edge("exp_understand", "exp_plan")
    workflow.add_edge("exp_design", "exp_plan")
    workflow.add_conditional_edges("exp_plan", route_after_plan, ["exp_setup", "exp_attempt"])
    workflow.add_conditional_edges("exp_setup", route_after_setup, ["exp_attempt", "exp_reflect"])
    workflow.add_edge("exp_attempt", "exp_reflect")
    workflow.add_conditional_edges("exp_reflect", route_after_report, ["exp_attempt", "exp_understand", "exp_plan", "synthesis"])
    workflow.add_edge("synthesis", "writer")
    workflow.add_edge("writer", "critic")
    workflow.add_edge("critic", "refinement")
    workflow.add_edge("refinement", "auditor")
    workflow.add_edge("auditor", END)
    
    # Compile with interrupts for human-in-the-loop
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["clarification", "planning", "assistance", "experiment_brief", "exp_scout", "exp_plan", "exp_reflect"]
    )

