"""The coding agent's toolbox: which tools each phase may use, how often, and how each is described to
the model. Steering the agent towards looking things up instead of guessing is most of what keeps an
experiment cheap; the limits stop a tool from becoming a loop of its own.

Editing, building and running code join the "code" phase with the sandbox."""
import functools
import inspect
from dataclasses import dataclass, field
from langchain_core.tools import StructuredTool
from langgraph.types import interrupt
from experiments import notebook as nb
from experiments.code_tools import CodeTools
from experiments.prior_work import search_literature, search_project_history

LOOKUP = ("repo_map", "outline", "find_definition", "find_references", "grep", "read_file")
PHASE_TOOLS = {
    "understand": LOOKUP + ("ask_user",),
    "plan": LOOKUP + ("search_literature", "search_project_history", "read_notebook", "check_already_tried", "ask_user"),
    "code": LOOKUP[1:] + ("read_notebook", "search_project_history", "edit_file", "write_file", "run_command", "quick_check"),
    "reflect": ("read_notebook", "read_file"),
}
LIMITS = {  # calls per phase
    "repo_map": 2, "outline": 20, "find_definition": 30, "find_references": 20, "grep": 20, "read_file": 30,
    "search_literature": 3, "search_project_history": 3, "read_notebook": 5, "check_already_tried": 10, "ask_user": 2,
    "edit_file": 40, "write_file": 10, "run_command": 15, "quick_check": 5,
}

DESCRIPTIONS = {
    "repo_map": "The most central files of the target and their key definitions. Start here. "
                "focus: space-separated words from the task, to rank the matching files first.",
    "outline": "Every function, class and type in one file, with line ranges. Use it before reading a file.",
    "find_definition": "Where a symbol (function, class, type, macro) is defined, with its signature.",
    "find_references": "Every place a symbol is used: its callers. Use it to see what a change would affect.",
    "grep": "Exact regex search over the target's text files; glob narrows it (e.g. '*.c'). For names, "
            "find_definition and find_references are more precise.",
    "read_file": "Lines start..end of a file, numbered (at most 200 per call). Read only what you need: "
                 "find the line range with outline or find_definition first.",
    "search_literature": "Papers (kind='papers') or practical articles and docs (kind='web') about an idea, "
                         "before you spend a run on it.",
    "search_project_history": "The target project's issues and pull requests about an idea: what maintainers "
                              "already tried, merged or rejected, and why.",
    "read_notebook": "Every earlier attempt: what it changed, whether the checks held, its result and lesson.",
    "check_already_tried": "Whether an idea was already attempted, so you never pay twice for the same failure.",
    "edit_file": "Replace one exact piece of text in a file (old must appear exactly once; copy it from read_file, "
                 "without the line numbers). Protected files are refused.",
    "write_file": "Create a new file, or replace a whole file. Prefer edit_file for changes to existing files.",
    "run_command": "Run a shell command in this attempt's sandbox (no network), e.g. compile, or run one test, to "
                   "find errors early. Output is cut to the last 3000 characters.",
    "quick_check": "Build, run the checks and take one measurement with the approved benchmark. Call it before you "
                   "finish: if it fails, fix the problem first.",
    "ask_user": "Ask the user something only they can answer: a decision, a preference, or a fact that is not in "
                "the code, the brief or the sources. Never ask what you can look up. One clear question.",
}


@dataclass
class ToolBudget:
    limits: dict = field(default_factory=lambda: dict(LIMITS))
    used: dict = field(default_factory=dict)

    def take(self, name: str) -> str | None:
        """None if the call may go ahead; otherwise the message the agent gets instead of a result."""
        self.used[name] = self.used.get(name, 0) + 1
        if self.used[name] > self.limits.get(name, 0):
            return (f"Limit reached: {name} can be used {self.limits.get(name, 0)} times in this phase. "
                    "Work with what you have, or finish this phase.")
        return None


@dataclass
class ToolContext:
    code: CodeTools
    target: str  # the brief's target, e.g. a repository URL
    goal: str  # the brief's metric goal: maximize or minimize
    notebook: list = field(default_factory=list)
    edits: object = None  # EditTools, in the code phase


def _ask_user(question: str) -> str:
    # Pauses the graph until the user answers; the tool runs again on resume and returns the answer
    return str(interrupt({"question": question}))


def _functions(ctx: ToolContext) -> dict:
    async def literature(query: str, kind: str = "papers") -> str:
        return await search_literature(query, kind)

    async def history(query: str) -> str:
        return await search_project_history(ctx.target, query)

    def notebook() -> str:
        return nb.render(ctx.notebook, ctx.goal)

    def already(idea: str) -> str:
        earlier = nb.already_tried(ctx.notebook, idea)
        return (f"Already tried as #{earlier['n']} [{earlier['verdict']}]: {earlier['hypothesis']}. "
                f"Lesson: {earlier.get('lesson') or 'none recorded'}") if earlier else "Not tried yet."

    return {"repo_map": ctx.code.repo_map, "outline": ctx.code.outline, "find_definition": ctx.code.find_definition,
            "find_references": ctx.code.find_references, "grep": ctx.code.grep, "read_file": ctx.code.read_file,
            "search_literature": literature, "search_project_history": history, "read_notebook": notebook,
            "check_already_tried": already, "ask_user": _ask_user,
            **({"edit_file": ctx.edits.edit_file, "write_file": ctx.edits.write_file, "run_command": ctx.edits.run_command,
                "quick_check": ctx.edits.quick_check} if ctx.edits else {})}


def _limited(name: str, func, budget: ToolBudget):
    """func behind the budget, with its signature kept so the model sees the real parameters."""
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def call(*args, **kwargs):
            return budget.take(name) or await func(*args, **kwargs)
    else:
        @functools.wraps(func)
        def call(*args, **kwargs):
            return budget.take(name) or func(*args, **kwargs)
    return call


def build_tools(phase: str, ctx: ToolContext, budget: ToolBudget | None = None) -> list[StructuredTool]:
    """The tools one phase may use, each counted against the phase's budget."""
    if phase not in PHASE_TOOLS:
        raise ValueError(f"Unknown phase {phase!r}; expected one of {', '.join(PHASE_TOOLS)}")
    if phase == "code" and ctx.edits is None:
        raise ValueError("The code phase needs EditTools (a sandbox and the approved benchmark)")
    budget, functions, tools = budget or ToolBudget(), _functions(ctx), []
    for name in PHASE_TOOLS[phase]:
        func = _limited(name, functions[name], budget)
        is_async = inspect.iscoroutinefunction(functions[name])
        tools.append(StructuredTool.from_function(func=None if is_async else func, coroutine=func if is_async else None,
                                                  name=name, description=DESCRIPTIONS[name]))
    return tools
