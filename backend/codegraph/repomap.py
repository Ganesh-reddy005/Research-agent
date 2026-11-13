"""A repo map: the most central files and their key definitions, within a token budget. It is
what the coding agent reads first, instead of opening files at random."""
from codegraph.graph import CodeGraph

CHARS_PER_TOKEN = 4
PER_FILE = 8  # definitions shown per file
MAP_KINDS = {"function", "method", "class", "struct", "enum", "interface", "type", "module"}


def repo_map(graph: CodeGraph, budget_tokens: int = 1500, focus: list[str] | None = None) -> str:
    budget, blocks, used = budget_tokens * CHARS_PER_TOKEN, [], 0
    for path, _ in graph.ranked_files(focus):
        symbols = graph.files[path]
        shown = sorted((d for d in symbols.definitions if d.kind in MAP_KINDS),
                       key=lambda d: (-graph.usage(d), d.line))[:PER_FILE]
        lines = [f"{path} ({symbols.lines} lines)"] + [f"  L{d.line}: {d.signature}" for d in sorted(shown, key=lambda d: d.line)]
        block = "\n".join(lines)
        if used + len(block) > budget:
            if blocks:
                break
            block = block[:budget]  # one huge file still gets a partial entry
        blocks.append(block)
        used += len(block) + 1
    remaining = len(graph.files) - len(blocks)
    tail = f"\n... {remaining} more files (use outline, find_definition or grep)" if remaining > 0 else ""
    return "\n".join(blocks) + tail
