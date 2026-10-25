"""The project a paper is about (from a repository), as agents see it.

A research session either explores a topic or writes up the authors' own project. Agents call
these helpers instead of reading project_profile themselves, so a new kind of project input
only has to produce the same profile shape."""


def is_project_paper(state) -> bool:
    return bool(state.get("project_profile"))


def _bullets(items) -> str:
    return "; ".join(str(i) for i in items) if isinstance(items, list) and items else "Not found in the repository"


def project_context(state) -> str:
    """The project profile as a prompt block, or '' for a topic-only session."""
    profile = state.get("project_profile")
    if not profile:
        return ""
    components = profile.get("architecture") or []
    architecture = "\n".join(
        f"- {c.get('component')}: {c.get('role')}" for c in components if isinstance(c, dict)
    ) or "- Not found in the repository"
    notes = state.get("project_notes")
    return f"""PROJECT BEING WRITTEN UP (the authors' own work, analysed from its repository {profile.get('name')}):
Summary: {profile.get('summary', '')}
Problem: {profile.get('problem', 'Not found in the repository')}
Approach: {profile.get('approach', 'Not found in the repository')}
Architecture:
{architecture}
Tech stack: {_bullets(profile.get('tech_stack'))}
Key algorithms: {_bullets(profile.get('key_algorithms'))}
Data: {_bullets(profile.get('data'))}
Evaluation in the repository: {profile.get('evaluation', 'Not found in the repository')}
Limitations: {_bullets(profile.get('limitations'))}""" + (f"\nAuthors' notes: {notes}" if notes else "")


def project_source(profile: dict) -> dict:
    """The repository as a citable source: it becomes reference [1] of a project paper."""
    owner = profile.get("name", "").split("/")[0]
    return {
        "title": f"{profile.get('name')}: {profile.get('title', '')}".rstrip(": "),
        "url": profile.get("url"),
        "summary": profile.get("summary", ""),
        "source": "GitHub",
        "authors": [owner] if owner else [],
        "year": int(profile["analysed_on"][:4]) if profile.get("analysed_on") else None,
        "kind": "project",
    }


def is_project_source(source: dict) -> bool:
    return source.get("kind") == "project"
