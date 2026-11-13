"""The code graph of a whole repository: where every symbol is defined, where it is used, and which
files matter most (ranked like PageRank: a file many others depend on ranks high)."""
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from codegraph.languages import supported
from codegraph.parser import Definition, FileSymbols, parse_file
from repo.filetypes import SKIP_DIRS, is_test

MAX_FILE_BYTES = 1_000_000  # larger sources are almost always generated
DAMPING = 0.85
ITERATIONS = 30
FOCUS_BOOST = 20.0  # how much more a focus file is worth as a starting point of the ranking
TEST_WEIGHT = 0.1  # tests rank below the code they test; they stay findable
# Bundled third-party code: not the project's own, and often huge
VENDORED_DIRS = {"vendors", "vendored", "3rdparty", "external", "extern", "deps"}
MIN_OUT = 1.0  # a file whose links add up to less passes on only that share of its rank
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


def words(name: str) -> set[str]:
    """quantize_row / QuantizeRow / quantizeRow -> {quantize, row}"""
    return {w.lower() for w in _WORD.findall(name)}


def specificity(name: str) -> float:
    """How strongly a use of this name points at its definition: parse_github_url or RepoRef surely
    does; a short generic name like url or run is mostly something else with the same name."""
    return 1.0 if len(name) >= 8 or len(words(name)) > 1 else 0.1


def source_files(root: Path):
    """Relative POSIX paths of the parseable source files under root, skipping vendored, built and hidden dirs."""
    for directory, subdirs, names in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS | VENDORED_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = Path(directory) / name
            if supported(name) and path.stat().st_size <= MAX_FILE_BYTES:
                yield path.relative_to(root).as_posix()


@dataclass
class CodeGraph:
    root: Path
    files: dict[str, FileSymbols] = field(default_factory=dict)
    definitions: dict[str, list[Definition]] = field(default_factory=lambda: defaultdict(list))
    references: dict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))

    @classmethod
    def build(cls, root) -> "CodeGraph":
        graph = cls(root=Path(root))
        for path in source_files(graph.root):
            symbols = parse_file(path, (graph.root / path).read_bytes())
            if symbols:
                graph.files[path] = symbols
                for definition in symbols.definitions:
                    graph.definitions[definition.name].append(definition)
        for path, symbols in graph.files.items():  # only names defined in the repository are worth tracking
            for name, lines in symbols.references.items():
                if name in graph.definitions:
                    graph.references[name].extend((path, line) for line in lines)
        return graph

    def update_file(self, path: str) -> None:
        """Re-read one file after an edit, so lookups stay true to the code."""
        source = self.root / path
        symbols = parse_file(path, source.read_bytes()) if source.is_file() else None
        self.files.pop(path, None)
        if symbols:
            self.files[path] = symbols
        self.definitions, self.references = defaultdict(list), defaultdict(list)
        for symbols in self.files.values():
            for definition in symbols.definitions:
                self.definitions[definition.name].append(definition)
        for file_path, symbols in self.files.items():
            for name, lines in symbols.references.items():
                if name in self.definitions:
                    self.references[name].extend((file_path, line) for line in lines)

    def find_definition(self, name: str) -> list[Definition]:
        return list(self.definitions.get(name, []))

    def similar_names(self, name: str, limit: int = 10) -> list[str]:
        """Defined names containing the text, for when an exact lookup finds nothing."""
        needle = name.lower()
        return sorted((n for n in self.definitions if needle in n.lower()), key=len)[:limit]

    def find_references(self, name: str) -> list[tuple[str, int]]:
        return sorted(self.references.get(name, []))

    def outline(self, path: str) -> list[Definition]:
        symbols = self.files.get(PurePosixPath(path).as_posix())
        return list(symbols.definitions) if symbols else []

    def usage(self, definition: Definition) -> int:
        """How often a symbol is referenced outside its own file: how central it is."""
        return sum(1 for path, _ in self.references.get(definition.name, []) if path != definition.path)

    def _edges(self) -> dict[str, dict[str, float]]:
        """file -> {file it depends on: weight}; a name defined in several files splits its weight.
        Real code never depends on tests, so a test's fake (say a `json` method) can't attract its uses."""
        edges = defaultdict(lambda: defaultdict(float))
        for path, symbols in self.files.items():
            from_test = is_test(path)
            for name, lines in symbols.references.items():
                targets = {d.path for d in self.definitions.get(name, []) if from_test or not is_test(d.path)} - {path}
                for target in targets:
                    edges[path][target] += specificity(name) * len(lines) ** 0.5 / len(targets)
        return edges

    def _matches_focus(self, path: str, focus: list[str]) -> bool:
        """A focus word in the file's path, or a whole word of one of its definitions' names."""
        if any(word in path.lower() for word in focus):
            return True
        defined = set().union(*(words(d.name) for d in self.files[path].definitions)) if self.files[path].definitions else set()
        return any(word in defined for word in focus)

    def ranked_files(self, focus: list[str] | None = None) -> list[tuple[str, float]]:
        """Files from most to least central. With focus words (task terms, symbol or file names), the files
        that match come first, and the ranking starts from them so their neighbourhood comes next."""
        paths = list(self.files)
        if not paths:
            return []
        focus = [w.lower() for w in focus or [] if len(w) > 2]
        matched = {p for p in paths if focus and self._matches_focus(p, focus)}
        weight = {p: (FOCUS_BOOST if p in matched else 1.0) * (TEST_WEIGHT if is_test(p) else 1.0) for p in paths}
        start = {p: w / sum(weight.values()) for p, w in weight.items()}
        rank = self._pagerank(paths, start)
        score = {p: r * (TEST_WEIGHT if is_test(p) else 1.0) + (1.0 if p in matched else 0.0) for p, r in rank.items()}
        return sorted(score.items(), key=lambda item: (-item[1], item[0]))

    def _pagerank(self, paths: list[str], start: dict[str, float]) -> dict[str, float]:
        edges, rank = self._edges(), dict(start)
        for _ in range(ITERATIONS):
            nxt = {p: (1 - DAMPING) * start[p] for p in paths}
            # Rank not passed along links (no links, or only weak ones) restarts like a random jump
            spread = sum(rank[p] * (1 - min(sum(edges[p].values()), MIN_OUT) / MIN_OUT) if p in edges else rank[p]
                         for p in paths)
            for p in paths:
                nxt[p] += DAMPING * spread * start[p]
            for source, targets in edges.items():
                out = max(sum(targets.values()), MIN_OUT)
                for target, weight in targets.items():
                    nxt[target] += DAMPING * rank[source] * weight / out
            rank = nxt
        return rank
