"""One phase of the coding agent: LangGraph's prebuilt tool-calling agent with that phase's tools, budget
and step limit. It returns the JSON object of its final message, plus the tokens it used."""
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent
from experiments.brief import json_object
from experiments.toolbox import ToolBudget, ToolContext, build_tools
from utils.llm import get_llm

MAX_STEPS = {"scout": 10, "design": 15, "understand": 25, "plan": 15, "code": 40}  # model turns per phase
MAX_TOKENS = 8000  # per model reply
TRACE_CHARS = 160  # per tool call in the trace
REPAIR = "Your final message wasn't a valid JSON object. Reply with ONLY that JSON object, exactly as specified, nothing else."
STEPS_PER_TURN = 3  # graph steps per model turn: the wrap-up hook, the model, the tools
OUT_OF_STEPS_REPLY = "Sorry, need more steps"  # LangGraph's own last reply when the limit cuts off a tool call
WRAP_UP_TURNS = 2  # turns before the limit at which the agent is told to stop exploring and answer
WRAP_UP = ("You have {turns} turn(s) left. Stop calling tools now: reply with ONLY the final JSON object, as specified, "
           "using what you have found so far. Leave fields you couldn't work out empty and say what's missing.")
OUT_OF_STEPS = ("You are out of steps. Reply with ONLY the final JSON object, as specified, using what you have found "
                "so far. Leave fields you couldn't work out empty and say what's missing.")


async def run_phase(phase: str, agent_name: str, system: str, task: str, ctx: ToolContext) -> tuple[dict, dict]:
    """(final JSON, token usage by model). Near the step limit the agent is told to answer; if it still runs out,
    one call without tools answers from what it found, and only when that fails is the result {"error": ...}.
    An ask_user interrupt propagates: the graph pauses, and on resume this phase continues where it was."""
    usage = UsageMetadataCallbackHandler()
    llm, tools = get_llm(agent_name, streaming=False, max_tokens=MAX_TOKENS), build_tools(phase, ctx, ToolBudget())
    agent = create_react_agent(llm, tools, prompt=system, pre_model_hook=_wrap_up_hook)
    config = {"recursion_limit": STEPS_PER_TURN * MAX_STEPS[phase] + 1, "callbacks": [usage]}
    out, ran_out = {"messages": []}, False
    try:  # streamed, so what the agent did survives a stop at the step limit
        async for out in agent.astream({"messages": [HumanMessage(content=task)]}, config=config, stream_mode="values"):
            pass
    except GraphRecursionError:
        ran_out = True
    messages = out["messages"]
    if messages and isinstance(messages[-1], AIMessage) and _text(messages[-1]).startswith(OUT_OF_STEPS_REPLY):
        messages, ran_out = messages[:-1], True
    trace = tool_trace(messages)
    text = "" if ran_out else _text(messages[-1])
    result = json_object(text)
    if not result:  # out of steps, or the answer wasn't JSON: one call without tools, over everything it found
        final = llm.bind_tools(tools, tool_choice="none")
        prompt = [SystemMessage(content=system), *answered(messages), HumanMessage(content=OUT_OF_STEPS if ran_out else REPAIR)]
        text = _text(await final.ainvoke(prompt, config={"callbacks": [usage]}))
        result = json_object(text)
    if not result:
        result = {"error": f"stopped after {MAX_STEPS[phase]} steps without a final answer" if ran_out
                  else "the final answer wasn't valid JSON", "raw": text[-1500:]}
    elif ran_out:
        result = {**result, "note": f"answered at the {MAX_STEPS[phase]}-step limit, from what it had found"}
    return {**result, "trace": trace}, usage.usage_metadata


def _wrap_up_hook(state) -> dict:
    """Before each model turn: near the step limit, tell the model to answer now (not saved to the history)."""
    turns = state.get("remaining_steps", 99) // STEPS_PER_TURN
    if turns > WRAP_UP_TURNS:
        return {"llm_input_messages": state["messages"]}
    return {"llm_input_messages": [*state["messages"], HumanMessage(content=WRAP_UP.format(turns=max(turns, 1)))]}


def answered(messages) -> list:
    """The conversation without a trailing model turn whose tool calls never got answers (a provider rejects those)."""
    answers = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    end = len(messages)
    while end and isinstance(messages[end - 1], AIMessage) and any(c["id"] not in answers for c in messages[end - 1].tool_calls or []):
        end -= 1
    return list(messages[:end])


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
