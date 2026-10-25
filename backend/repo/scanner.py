"""Turn a repository's raw files into a RepoSnapshot: decoded source files, the README,
dependency manifests, a file tree, line counts per language, and the files that matter most."""
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath

from repo.filetypes import ENTRY_POINT_STEMS, classify, is_code, is_readme, is_test


@dataclass
class SourceFile:
    path: str
    language: str  # a programming language, or 'Markdown', 'Manifest', 'Config'
    text: str

    @property
    def lines(self) -> int:
        return self.text.count("\n") + 1


@dataclass
class RepoSnapshot:
    files: list[SourceFile]
    readme: str
    manifests: dict[str, str]
    tree: str
    languages: dict[str, int]  # lines of code per programming language, largest first

    @property
    def code_files(self) -> list[SourceFile]:
        return [f for f in self.files if is_code(f.language)]

    @property
    def total_lines(self) -> int:
        return sum(self.languages.values())


def notebook_text(raw: str) -> str:
    """A Jupyter notebook's markdown and code cells as plain text (outputs dropped)."""
    try:
        cells = json.loads(raw).get("cells", [])
    except (json.JSONDecodeError, AttributeError):
        return ""
    parts = []
    for cell in cells:
        source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        if source.strip():
            parts.append(f"# [{cell.get('cell_type', 'code')} cell]\n{source}")
    return "\n\n".join(parts)


def decode(path: str, data: bytes) -> SourceFile | None:
    language = classify(path)
    if not language or b"\0" in data[:4096]:  # a NUL byte means binary
        return None
    text = data.decode("utf-8", errors="replace")
    if path.endswith(".ipynb"):
        text = notebook_text(text)
    return SourceFile(path, language, text) if text.strip() else None


def file_tree(paths: list[str], limit: int = 150) -> str:
    """Every path when the repository is small; otherwise folders with their file counts."""
    if len(paths) <= limit:
        return "\n".join(sorted(paths))
    folders = Counter(str(PurePosixPath(p).parent) for p in paths)
    lines = [f"{folder}/ ({count} files)" for folder, count in sorted(folders.items())]
    return "\n".join(lines[:limit]) + (f"\n... and {len(lines) - limit} more folders" if len(lines) > limit else "")


def build_snapshot(raw_files: list[tuple[str, bytes]]) -> RepoSnapshot:
    files = [f for f in (decode(path, data) for path, data in raw_files) if f]
    depth = lambda f: len(PurePosixPath(f.path).parts)
    readmes = sorted((f for f in files if is_readme(f.path)), key=depth)
    languages = Counter()
    for f in files:
        if is_code(f.language):
            languages[f.language] += f.lines
    return RepoSnapshot(
        files=files,
        readme=readmes[0].text if readmes else "",
        manifests={f.path: f.text for f in files if f.language == "Manifest"},
        tree=file_tree([f.path for f in files]),
        languages=dict(languages.most_common()),
    )


def _importance(f: SourceFile, readme: str) -> tuple:
    p = PurePosixPath(f.path)
    return (
        p.name in readme,                     # files the README talks about
        p.stem.lower() in ENTRY_POINT_STEMS,  # entry points and core modules
        -len(p.parts),                        # nearer the root
        f.lines,                              # then bigger files
    )


def key_files(snapshot: RepoSnapshot, budget: int = 24_000, per_file: int = 4_000) -> list[tuple[str, str]]:
    """The most informative source files as (path, excerpt), within a character budget.
    Tests are left out: they describe how the code is checked, not what it does."""
    ranked = sorted((f for f in snapshot.code_files if not is_test(f.path)),
                    key=lambda f: _importance(f, snapshot.readme), reverse=True)
    picked, used = [], 0
    for f in ranked:
        excerpt = f.text[:per_file]
        if used + len(excerpt) > budget:
            break
        picked.append((f.path, excerpt))
        used += len(excerpt)
    return picked
