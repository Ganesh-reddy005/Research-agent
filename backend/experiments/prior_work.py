"""What others already know about an idea, before the agent spends a run on it: papers and articles
(the same providers the retriever uses), and the target project's own issues and pull requests, where
maintainers often explain what was tried, what was merged and what was rejected."""
import re
import httpx
from agents.retriever import run_need
from repo.github import RepoError, api_headers, parse_github_url

PER_PROVIDER = 3
MAX_RESULTS = 6
SUMMARY_CHARS = 240
ISSUES_API = "https://api.github.com/search/issues"


def _clip(text) -> str:
    text = " ".join(str(text or "").split())
    return text[:SUMMARY_CHARS] + ("…" if len(text) > SUMMARY_CHARS else "")


async def search_literature(query: str, kind: str = "papers") -> str:
    """Papers (kind="papers") or practical articles and docs (kind="web") about an idea."""
    kind = kind if kind in {"papers", "web"} else "papers"
    sources = (await run_need({"query": query, "kind": kind}, None, PER_PROVIDER))[:MAX_RESULTS]
    if not sources:
        return f"Nothing found for {query!r} ({kind})."
    return "\n".join(f"- {s.get('title')} ({s.get('year') or 'n.d.'}) {s.get('url')}\n  {_clip(s.get('summary'))}"
                     for s in sources)


async def search_project_history(target: str, query: str) -> str:
    """Issues and pull requests of the target repository that discuss the idea."""
    try:
        repo = parse_github_url(target)
    except RepoError:
        return "The target isn't a GitHub repository, so there is no issue history to search."
    params = {"q": f"repo:{repo.full_name} {query}", "per_page": MAX_RESULTS, "sort": "reactions"}
    async with httpx.AsyncClient(headers=api_headers(None), timeout=15) as client:
        response = await client.get(ISSUES_API, params=params)
    if response.status_code in (403, 429):
        return "GitHub's search rate limit was reached; try again later or continue without it."
    if response.status_code != 200:
        return f"GitHub search failed ({response.status_code})."
    items = response.json().get("items", [])
    if not items:
        return f"No issues or pull requests in {repo.full_name} mention {query!r}."
    lines = []
    for item in items:
        kind = "PR" if item.get("pull_request") else "issue"
        merged = " merged" if (item.get("pull_request") or {}).get("merged_at") else ""
        lines.append(f"- {kind} #{item['number']} [{item.get('state')}{merged}] {item.get('title')} {item.get('html_url')}\n"
                     f"  {_clip(item.get('body'))}")
    return "\n".join(lines)


REPOS_API = "https://api.github.com/search/repositories"
_GITHUB_REPO = re.compile(r"https?://github\.com/([\w.-]+)/([\w.-]+)")


async def search_repositories(query: str) -> str:
    """Existing open-source code for an idea, most-starred first, with activity and license."""
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": MAX_RESULTS}
    async with httpx.AsyncClient(headers=api_headers(None), timeout=15) as client:
        response = await client.get(REPOS_API, params=params)
    if response.status_code in (403, 429):
        return "GitHub's search rate limit was reached; try again later or continue without it."
    if response.status_code != 200:
        return f"GitHub search failed ({response.status_code})."
    items = response.json().get("items", [])
    if not items:
        return f"No repositories found for {query!r}."
    return "\n".join(f"- {r['html_url']} ★{r.get('stargazers_count', 0):,} · last push {str(r.get('pushed_at', ''))[:10]} · "
                     f"{(r.get('license') or {}).get('spdx_id') or 'no license'} · {r.get('language') or '?'}\n  {_clip(r.get('description'))}"
                     for r in items)


def repositories_in_sources(sources: list[dict]) -> list[str]:
    """GitHub repositories the research already found: papers' code links, cited projects."""
    found = []
    for source in sources:
        for text in (source.get("url") or "", source.get("summary") or ""):
            for owner, name in _GITHUB_REPO.findall(text):
                url = f"https://github.com/{owner}/{name.removesuffix('.git').rstrip('.')}"
                if url not in found:
                    found.append(url)
    return found[:MAX_RESULTS * 2]
