"""The target's code on the host: cloned once at a pinned commit, and every attempt saved as a git
commit, so each change has an exact diff and going back to the baseline is free.

The sandbox mounts this folder; the agent's code tools read it."""
import os
import subprocess
from pathlib import Path

WORKSPACES = Path(os.getenv("LUME_WORKSPACES", Path.home() / ".lume" / "workspaces"))
# Lume's commits need an identity, and no hook from the target may ever run on the host
GIT = ["git", "-c", "user.name=Lume", "-c", "user.email=lume@localhost", "-c", "commit.gpgsign=false",
       "-c", "core.hooksPath=/dev/null"]
MAX_DIFF_CHARS = 20_000
# Caches, build output and backup copies never belong in an attempt's diff (git already keeps every version)
EXCLUDE = "__pycache__/\n*.pyc\n.pytest_cache/\n*.bak\n*.orig\n*.rej\n*~\n*.swp\n"


def workspace_path(name: str) -> Path:
    """Where a session's workspace lives, looked up at call time (so tests can redirect WORKSPACES)."""
    return WORKSPACES / name


class WorkspaceError(Exception):
    pass


class Workspace:
    def __init__(self, path):
        self.path = Path(path)

    def git(self, *args: str) -> str:
        result = subprocess.run([*GIT, *args], cwd=self.path, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            raise WorkspaceError(f"git {args[0]} failed: {result.stderr.strip()[-500:]}")
        return result.stdout

    def git_bytes(self, *args: str) -> bytes:
        """A git command's raw output (e.g. an archive)."""
        result = subprocess.run([*GIT, *args], cwd=self.path, capture_output=True, stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            raise WorkspaceError(f"git {args[0]} failed: {result.stderr.decode(errors='replace').strip()[-500:]}")
        return result.stdout

    @classmethod
    def clone(cls, source: str, name: str, ref: str | None = None) -> "Workspace":
        """A fresh copy of source (a repository URL or a local git folder) at ref, or its default branch."""
        path = workspace_path(name)
        if path.exists():
            raise WorkspaceError(f"A workspace named {name} already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([*GIT, "clone", "--quiet", "--no-recurse-submodules", source, str(path)],
                                capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if result.returncode != 0:
            raise WorkspaceError(f"Couldn't clone {source}: {result.stderr.strip()[-500:]}")
        workspace = cls(path)
        (path / ".git" / "info" / "exclude").write_text(EXCLUDE)
        if ref:
            workspace.git("checkout", "--quiet", ref)
        return workspace

    @classmethod
    def create(cls, name: str) -> "Workspace":
        """An empty workspace, for code written from scratch."""
        path = workspace_path(name)
        if path.exists():
            raise WorkspaceError(f"A workspace named {name} already exists")
        path.mkdir(parents=True)
        subprocess.run([*GIT, "init", "--quiet", str(path)], check=True, capture_output=True, stdin=subprocess.DEVNULL)
        (path / ".git" / "info" / "exclude").write_text(EXCLUDE)
        workspace = cls(path)
        workspace.snapshot("empty workspace")
        return workspace

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    def snapshot(self, message: str) -> str:
        """Save the current files as a commit (even if nothing changed) and return its id."""
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "--no-verify", "-m", message)
        return self.head()

    def diff(self, base: str, head: str = "HEAD") -> str:
        text = self.git("diff", base, head)
        return text if len(text) <= MAX_DIFF_CHARS else text[:MAX_DIFF_CHARS] + "\n[... diff truncated]"

    def changed_files(self, base: str, head: str = "HEAD") -> list[str]:
        return [line for line in self.git("diff", "--name-only", base, head).splitlines() if line]

    def reset(self, commit: str) -> None:
        """Back to a saved commit; untracked files go too, ignored build output stays (it is a cache)."""
        self.git("reset", "--quiet", "--hard", commit)
        self.git("clean", "--quiet", "-fd")
