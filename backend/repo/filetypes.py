"""What kind of file a repository path is, and whether it's worth reading."""
from pathlib import PurePosixPath

MAX_FILE_BYTES = 200_000  # bigger files are almost always generated or data

CODE_LANGUAGES = {
    ".py": "Python", ".ipynb": "Jupyter Notebook", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java", ".kt": "Kotlin", ".go": "Go",
    ".rs": "Rust", ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".cs": "C#",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".scala": "Scala", ".r": "R", ".m": "MATLAB",
    ".jl": "Julia", ".dart": "Dart", ".lua": "Lua", ".sh": "Shell", ".sql": "SQL", ".vue": "Vue",
    ".svelte": "Svelte", ".sol": "Solidity", ".cu": "CUDA",
}
DOC_SUFFIXES = {".md", ".rst", ".txt"}
CONFIG_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"}

# Dependency and build files: they reveal the tech stack
MANIFESTS = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "environment.yml",
    "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile",
    "composer.json", "Dockerfile", "docker-compose.yml", "CMakeLists.txt", "Makefile",
}

SKIP_DIRS = {
    "node_modules", "dist", "build", "out", "target", "vendor", "venv", "env", "site-packages",
    "__pycache__", "coverage", "bower_components", "Pods", "third_party", "migrations",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "Gemfile.lock",
    "composer.lock", "uv.lock", "go.sum", "Pipfile.lock",
}

# Names that usually hold a project's core logic or its entry point
ENTRY_POINT_STEMS = {"main", "app", "index", "server", "train", "model", "models", "cli", "run", "pipeline", "core"}


def is_readme(path: str) -> bool:
    return PurePosixPath(path).name.lower().startswith("readme")


def classify(path: str) -> str | None:
    """'Python', 'Markdown', 'Manifest', 'Config', or None for files Lume doesn't read."""
    p = PurePosixPath(path)
    suffix = p.suffix.lower()
    if p.name in MANIFESTS:
        return "Manifest"
    if suffix in CODE_LANGUAGES:
        return CODE_LANGUAGES[suffix]
    if suffix in DOC_SUFFIXES or is_readme(path):
        return "Markdown"
    if suffix in CONFIG_SUFFIXES:
        return "Config"
    return None


def should_read(path: str, size: int) -> bool:
    """The include filter for a repository fetch: source, docs and manifests, nothing generated."""
    p = PurePosixPath(path)
    if size > MAX_FILE_BYTES or p.name in SKIP_FILES or p.name.endswith((".min.js", ".map")):
        return False
    if any(part in SKIP_DIRS or part.startswith(".") for part in p.parts[:-1]):
        return False
    return classify(path) is not None


def is_code(language: str) -> bool:
    return language in CODE_LANGUAGES.values()


def is_test(path: str) -> bool:
    p = PurePosixPath(path)
    return any(part in {"test", "tests", "__tests__", "spec"} for part in p.parts[:-1]) or \
        p.stem.startswith("test_") or p.stem.endswith(("_test", ".test", ".spec"))
