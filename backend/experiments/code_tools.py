"""The coding agent's ways of looking at the target code. Each answer is compact text with a hard cap,
because every line the agent reads costs tokens: it should look things up, not read whole files."""
import shutil
import subprocess
import sys
from pathlib import Path
from codegraph.graph import CodeGraph, VENDORED_DIRS
from codegraph.repomap import repo_map
from repo.filetypes import SKIP_DIRS

MAX_READ_LINES = 200
MAX_MATCHES = 40
MAX_OUTLINE = 80
GREP_TIMEOUT = 20  # seconds
# ripgrep comes from the `ripgrep` package, next to the Python running the app; else from PATH
RG = shutil.which("rg", path=str(Path(sys.executable).parent)) or shutil.which("rg")
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

    def grep(self, pattern: str, glob: str = "") -> str:
        """Regex search over text files (optionally only those matching glob, e.g. '*.c'), with ripgrep:
        fast, skips binary, hidden and .gitignored files."""
        excluded = [f"!{d}/" for d in sorted(SKIP_DIRS | VENDORED_DIRS)]
        command = [RG or "rg", "--line-number", "--no-heading", "--color", "never", "--max-filesize", "1M",
                   *(arg for d in excluded for arg in ("-g", d)), *(["-g", glob] if glob else []), "-e", pattern, "."]  # an explicit path: without one, rg reads stdin
        try:
            result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=GREP_TIMEOUT,
                                    stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            return "grep needs ripgrep (rg) installed on the server."
        except subprocess.TimeoutExpired:
            return f"Search took over {GREP_TIMEOUT}s; narrow the pattern or glob."
        if result.returncode == 2:  # rg's exit code for errors, such as an invalid pattern
            return f"Invalid pattern: {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else pattern}"
        found = result.stdout.splitlines()
        if not found:
            return f"No matches for {pattern}."
        shown = []
        for line in found[:MAX_MATCHES]:
            path, number, text = line.removeprefix("./").split(":", 2)
            shown.append(f"{path}:{number}: {text.strip()[:160]}")
        more = len(found) - MAX_MATCHES
        return "\n".join(shown) + (f"\n... {more} more matches; narrow the pattern or glob" if more > 0 else "")
