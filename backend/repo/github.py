"""GitHub as a repository provider: parse a repository link and fetch its files over the REST API.

The tarball is read in memory. Nothing from the repository is written to disk or executed."""
import io
import os
import re
import tarfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import httpx

API = "https://api.github.com"
MAX_ARCHIVE_BYTES = 60 * 1024 * 1024    # compressed download
MAX_READ_BYTES = 15 * 1024 * 1024       # total size of the files actually read


class RepoError(Exception):
    """The repository can't be fetched. The message is safe to show the user."""


@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str
    ref: str | None = None  # branch, tag or commit; None means the default branch

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.full_name}"


@dataclass
class FetchedRepo:
    repo: RepoRef
    branch: str
    commit: str
    description: str = ""
    topics: list[str] = field(default_factory=list)
    license: str | None = None
    stars: int = 0
    files: list[tuple[str, bytes]] = field(default_factory=list)  # (path inside the repo, content)
    skipped: int = 0  # files left out by the include filter or the size limits


_OWNER = r"[A-Za-z0-9-]+"
_NAME = r"[A-Za-z0-9_.-]+?"
# github.com/owner/repo, optionally .git, /tree/<ref>, or any other page of the repo
_URL = re.compile(
    rf"^(?:https?://)?(?:www\.)?github\.com/({_OWNER})/({_NAME})(?:\.git)?"
    rf"(?:/tree/([^?#]+?)|/[^?#]*)?/?(?:[?#].*)?$"
)
_SHORTHAND = re.compile(rf"^({_OWNER})/({_NAME})(?:\.git)?$")


def parse_github_url(url: str) -> RepoRef:
    """'https://github.com/owner/repo/tree/dev' or 'owner/repo' -> RepoRef."""
    text = (url or "").strip()
    match = _URL.match(text) or _SHORTHAND.match(text)
    if not match:
        raise RepoError("Enter a GitHub repository link like https://github.com/owner/repo")
    owner, name, *rest = match.groups()
    ref = rest[0] if rest else None
    return RepoRef(owner, name, ref.strip("/") if ref else None)


def _headers(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _check(response: httpx.Response, repo: RepoRef) -> None:
    if response.status_code == 404:
        raise RepoError(f"Couldn't find {repo.full_name} on GitHub. Check the link; private repositories aren't supported yet.")
    if response.status_code in (403, 429):
        raise RepoError("GitHub's rate limit was reached. Try again in a few minutes.")
    response.raise_for_status()


async def fetch_repo(repo: RepoRef, include: Callable[[str, int], bool], token: str | None = None) -> FetchedRepo:
    """Download the repository and read the files `include(path, size)` accepts."""
    async with httpx.AsyncClient(headers=_headers(token), timeout=30, follow_redirects=True) as client:
        meta = await client.get(f"{API}/repos/{repo.full_name}")
        _check(meta, repo)
        info = meta.json()
        branch = repo.ref or info.get("default_branch") or "main"
        archive = await _download(client, f"{API}/repos/{repo.full_name}/tarball/{branch}", repo)

    files, skipped, commit = read_archive(archive, include)
    return FetchedRepo(
        repo=repo, branch=branch, commit=commit,
        description=info.get("description") or "",
        topics=info.get("topics") or [],
        license=(info.get("license") or {}).get("spdx_id"),
        stars=info.get("stargazers_count") or 0,
        files=files, skipped=skipped,
    )


async def _download(client: httpx.AsyncClient, url: str, repo: RepoRef) -> bytes:
    async with client.stream("GET", url) as response:
        _check(response, repo)
        buffer = bytearray()
        async for chunk in response.aiter_bytes():
            buffer.extend(chunk)
            if len(buffer) > MAX_ARCHIVE_BYTES:
                raise RepoError(f"{repo.full_name} is too large: over {MAX_ARCHIVE_BYTES // 2**20} MB compressed.")
        return bytes(buffer)


def _safe_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and not path.startswith("/") and ".." not in parts


def read_archive(archive: bytes, include: Callable[[str, int], bool]) -> tuple[list[tuple[str, bytes]], int, str]:
    """Regular files from a GitHub tarball as (path, content), how many were skipped, and the commit.

    GitHub wraps everything in one '<owner>-<repo>-<sha>/' folder; paths are returned without it.
    Links, devices and anything outside the repository are ignored."""
    files, skipped, total, root = [], 0, 0, ""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as tar:
            for member in tar:
                top, _, path = member.name.partition("/")
                root = root or top
                if not member.isfile() or not _safe_path(path):
                    continue
                if not include(path, member.size) or total + member.size > MAX_READ_BYTES:
                    skipped += 1
                    continue
                data = tar.extractfile(member).read()
                total += len(data)
                files.append((path, data))
    except tarfile.TarError as e:
        raise RepoError("GitHub sent an archive that couldn't be read.") from e
    return files, skipped, root.rsplit("-", 1)[-1] if "-" in root else ""


def is_transient(exc: Exception) -> bool:
    """Worth retrying: network failures and GitHub 5xx errors. Never a RepoError (bad link, too large)."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)
