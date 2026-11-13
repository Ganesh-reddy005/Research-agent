"""One phase of the coding agent: LangGraph's prebuilt tool-calling agent with that phase's tools, budget
and step limit. It returns the JSON object of its final message, plus the tokens it used."""
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent
from experiments.brief import json_object
from experiments.toolbox import ToolBudget, ToolContext, build_tools
from utils.llm import get_llm

MAX_STEPS = {"understand": 25, "plan": 15, "code": 40}  # model turns per phase
MAX_TOKENS = 8000  # per model reply


async def run_phase(phase: str, agent_name: str, system: str, task: str, ctx: ToolContext) -> tuple[dict, dict]:
    """(final JSON, token usage by model). Hitting the step limit returns {"error": ...} rather than failing.
    An ask_user interrupt propagates: the graph pauses, and on resume this phase continues where it was."""
    usage = UsageMetadataCallbackHandler()
    agent = create_react_agent(get_llm(agent_name, streaming=False, max_tokens=MAX_TOKENS),
                               build_tools(phase, ctx, ToolBudget()), prompt=system)
    config = {"recursion_limit": 2 * MAX_STEPS[phase] + 1, "callbacks": [usage]}
    try:
        out = await agent.ainvoke({"messages": [HumanMessage(content=task)]}, config=config)
    except GraphRecursionError:
        return {"error": f"stopped after {MAX_STEPS[phase]} steps without a final answer"}, usage.usage_metadata
    content = out["messages"][-1].content
    text = content if isinstance(content, str) else " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return json_object(text) or {"error": "the final answer wasn't valid JSON", "raw": text[-1500:]}, usage.usage_metadata
