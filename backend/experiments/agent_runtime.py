"""One phase of the coding agent: LangGraph's prebuilt tool-calling agent with that phase's tools, budget
and step limit. It returns the JSON object of its final message, plus the tokens it used."""
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent
from experiments.brief import json_object
from experiments.toolbox import ToolBudget, ToolContext, build_tools
from utils.llm import get_llm

MAX_STEPS = {"scout": 10, "design": 15, "understand": 25, "plan": 15, "code": 40}  # model turns per phase
MAX_TOKENS = 8000  # per model reply
TRACE_CHARS = 160  # per tool call in the trace
REPAIR = "Your final message wasn't a valid JSON object. Reply with ONLY that JSON object, exactly as specified, nothing else."


async def run_phase(phase: str, agent_name: str, system: str, task: str, ctx: ToolContext) -> tuple[dict, dict]:
    """(final JSON, token usage by model). Hitting the step limit returns {"error": ...} rather than failing.
    An ask_user interrupt propagates: the graph pauses, and on resume this phase continues where it was."""
    usage = UsageMetadataCallbackHandler()
    agent = create_react_agent(get_llm(agent_name, streaming=False, max_tokens=MAX_TOKENS),
                               build_tools(phase, ctx, ToolBudget()), prompt=system)
    config = {"recursion_limit": 2 * MAX_STEPS[phase] + 1, "callbacks": [usage]}
    out = {"messages": []}
    try:  # streamed, so what the agent did survives a stop at the step limit
        async for out in agent.astream({"messages": [HumanMessage(content=task)]}, config=config, stream_mode="values"):
            pass
    except GraphRecursionError:
        return ({"error": f"stopped after {MAX_STEPS[phase]} steps without a final answer",
                 "trace": tool_trace(out["messages"])}, usage.usage_metadata)
    trace = tool_trace(out["messages"])
    text = _text(out["messages"][-1])
    result = json_object(text)
    if not result:  # one cheap retry, without tools, before giving up
        llm = get_llm(agent_name, streaming=False, max_tokens=MAX_TOKENS)
        repaired = await llm.ainvoke([*out["messages"][-6:], HumanMessage(content=REPAIR)], config={"callbacks": [usage]})
        result = json_object(_text(repaired))
    result = result or {"error": "the final answer wasn't valid JSON", "raw": text[-1500:]}
    return {**result, "trace": trace}, usage.usage_metadata


def tool_trace(messages) -> list[dict]:
    """What the agent did, step by step: each tool call with its arguments and the start of its answer."""
    answers = {getattr(m, "tool_call_id", None): _text(m) for m in messages if isinstance(m, ToolMessage)}
    trace = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            args = ", ".join(f"{k}={str(v)[:60]!s}" for k, v in (call.get("args") or {}).items())
            trace.append({"tool": call["name"], "args": args[:TRACE_CHARS],
                          "result": " ".join(answers.get(call.get("id"), "").split())[:TRACE_CHARS]})
    return trace


def _text(message) -> str:
    content = message.content
    return content if isinstance(content, str) else " ".join(c.get("text", "") for c in content if isinstance(c, dict))
