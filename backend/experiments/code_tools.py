"""The coding agent's ways of looking at the target code. Each answer is compact text with a hard cap,
because every line the agent reads costs tokens: it should look things up, not read whole files."""
import os
import re
from pathlib import Path
from codegraph.graph import CodeGraph, VENDORED_DIRS
from codegraph.repomap import repo_map
from repo.filetypes import SKIP_DIRS

MAX_READ_LINES = 200
MAX_MATCHES = 40
MAX_OUTLINE = 80
MAX_TEXT_BYTES = 1_000_000
MAX_MAP_TOKENS = 3000


class CodeTools:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.graph = CodeGraph.build(self.root)

    def _resolve(self, path: str) -> Path | None:
        """The file inside the target, or None for anything outside it (../, absolute paths, links)."""
        target = (self.root / path).resolve()
        return target if target.is_relative_to(self.root) and target.is_file() else None

    def repo_map(self, focus: str = "", budget_tokens: int = 1500) -> str:
        return repo_map(self.graph, budget_tokens=min(budget_tokens, MAX_MAP_TOKENS), focus=focus.split())

    def outline(self, path: str) -> str:
        definitions = self.graph.outline(path)
        if not definitions:
            return f"No definitions found in {path} (not a parsed source file, or wrong path)."
        if len(definitions) > MAX_OUTLINE:  # big files: functions and types before macros
            definitions = sorted(sorted(definitions, key=lambda d: d.kind == "macro")[:MAX_OUTLINE], key=lambda d: d.line)
        lines = [f"L{d.line}-{d.end_line} {d.kind} {d.parent + '.' if d.parent else ''}{d.name}: {d.signature}"
                 for d in definitions]
        more = len(self.graph.outline(path)) - len(definitions)
        return "\n".join(lines) + (f"\n... {more} more (macros left out first)" if more > 0 else "")

    def find_definition(self, name: str) -> str:
        found = self.graph.find_definition(name)
        if not found:
            similar = self.graph.similar_names(name)
            return f"No definition of {name}." + (f" Similar names: {', '.join(similar)}" if similar else "")
        return "\n".join(f"{d.path}:{d.line}-{d.end_line} {d.kind}: {d.signature}" for d in found[:MAX_MATCHES])

    def find_references(self, name: str) -> str:
        found = self.graph.find_references(name)
        if not found:
            return f"No references to {name} in the parsed sources."
        shown = "\n".join(f"{path}:{line}" for path, line in found[:MAX_MATCHES])
        return shown + (f"\n... {len(found) - MAX_MATCHES} more" if len(found) > MAX_MATCHES else "")

    def read_file(self, path: str, start: int = 1, end: int = 0) -> str:
        """Lines start..end (1-based, inclusive), numbered; at most MAX_READ_LINES per call."""
        target = self._resolve(path)
        if target is None:
            return f"No such file in the target: {path}"
        lines = target.read_text(errors="replace").splitlines()
        start = max(start, 1)
        end = min(end or start + MAX_READ_LINES - 1, start + MAX_READ_LINES - 1, len(lines))
        body = "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
        return f"{path} lines {start}-{end} of {len(lines)}\n{body}"

    def _text_files(self, glob: str):
        for directory, subdirs, names in os.walk(self.root):
            subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS | VENDORED_DIRS and not d.startswith("."))
            for name in sorted(names):
                path = Path(directory) / name
                relative = path.relative_to(self.root)
                if (not glob or relative.match(glob)) and path.stat().st_size <= MAX_TEXT_BYTES:
                    yield relative.as_posix(), path

    def grep(self, pattern: str, glob: str = "") -> str:
        """Regex search over text files (optionally only those matching glob, e.g. '*.c')."""
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Invalid pattern: {e}"
        matches, total = [], 0
        for relative, path in self._text_files(glob):
            data = path.read_bytes()
            if b"\0" in data[:4096]:
                continue  # binary
            for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), start=1):
                if regex.search(line):
                    total += 1
                    if len(matches) < MAX_MATCHES:
                        matches.append(f"{relative}:{n}: {line.strip()[:160]}")
        if not matches:
            return f"No matches for {pattern}."
        return "\n".join(matches) + (f"\n... {total - MAX_MATCHES} more matches; narrow the pattern or glob" if total > MAX_MATCHES else "")
