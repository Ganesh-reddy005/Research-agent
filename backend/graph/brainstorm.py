import asyncio
from datetime import date
from typing import Annotated, List, TypedDict
from utils.events import emit_event
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from agents.brainstorm import BRAINSTORM_SYSTEM_PROMPT
from agents.search_tools import SEARCH_TOOLS, run_search, format_results, public_source
from utils.llm import get_llm, ainvoke_with_retry

# Search rounds allowed per user message before the model must answer
MAX_SEARCH_ROUNDS = 3

class BrainstormState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]

def current_turn(messages):
    """Messages after the latest user message."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].type == "human":
            return messages[i + 1:]
    return messages

def get_brainstorm_llm(allow_tools: bool = True):
    llm = get_llm(agent_name="brainstorm")
    return llm.bind_tools(SEARCH_TOOLS) if allow_tools else llm

def history_for_model(messages, searching_done: bool):
    """Earlier turns as plain question/answer pairs (their search results aren't resent).
    Once searching is done, the current turn's results are folded into the question as text:
    with no tool calls in the request, the model can't answer with tool-call markup."""
    start = max((i for i, m in enumerate(messages) if m.type == "human"), default=0)
    past = [m for m in messages[:start] if m.type == "human" or (m.type == "ai" and not m.tool_calls)]
    current = messages[start:]
    if not searching_done:
        return past + current
    results = "\n\n".join(m.content for m in current if m.type == "tool")
    question = current[0].content
    return past + [HumanMessage(content=(
        f"{question}\n\n--- Search results gathered for this question ---\n{results}\n\n"
        "Answer now using these results, citing them as [n]. No more searches are available."
    ))]

async def agent_node(state):
    rounds = sum(1 for m in current_turn(state["messages"]) if m.type == "ai" and m.tool_calls)
    searching_done = rounds >= MAX_SEARCH_ROUNDS
    llm = get_brainstorm_llm(allow_tools=not searching_done)
    system = SystemMessage(content=BRAINSTORM_SYSTEM_PROMPT + f"\nToday's date is {date.today().isoformat()}.")
    response = await ainvoke_with_retry(llm, [system] + history_for_model(state["messages"], searching_done), label="brainstorm")
    return {"messages": [response]}

async def tools_node(state):
    """Runs the requested searches in parallel and numbers sources [1..n] across the whole turn."""
    calls = state["messages"][-1].tool_calls
    # A paper found by several searches keeps one number for the whole turn
    known = {s["url"]: s["n"] for m in current_turn(state["messages"]) if m.type == "tool"
             for s in (m.artifact or {}).get("sources", [])}
    next_n = max(known.values(), default=0) + 1

    for c in calls:
        await emit_event("search_start", {"id": c["id"], "tool": c["name"], "query": c["args"].get("query", "")})
    results = await asyncio.gather(*(run_search(c["name"], c["args"]) for c in calls))

    messages = []
    for c, found in zip(calls, results):
        query = c["args"].get("query", "")
        numbered = []
        for s in found:
            if s["url"] not in known:
                known[s["url"]] = next_n
                next_n += 1
            if all(x["n"] != known[s["url"]] for x in numbered):
                numbered.append({**s, "n": known[s["url"]]})
        shown = [public_source(s) for s in numbered]
        await emit_event("search_end", {"id": c["id"], "tool": c["name"], "query": query, "sources": shown})
        messages.append(ToolMessage(
            content=format_results(numbered),
            tool_call_id=c["id"],
            name=c["name"],
            artifact={"tool": c["name"], "query": query, "sources": shown},
        ))
    return {"messages": messages}

def route_after_agent(state):
    return "tools" if getattr(state["messages"][-1], "tool_calls", None) else END

def build_brainstorm_graph(checkpointer=None):
    """Brainstorm chat: the model may search the web, arXiv and OpenAlex before answering.
    Runs on the shared checkpointer, so conversations (and their sources) are saved."""
    workflow = StateGraph(BrainstormState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", route_after_agent, ["tools", END])
    workflow.add_edge("tools", "agent")
    return workflow.compile(checkpointer=checkpointer)
