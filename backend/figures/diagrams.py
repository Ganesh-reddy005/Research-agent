"""Architecture and method diagrams. The model proposes only the content (boxes and arrows, as JSON);
the Mermaid source is compiled here, so a diagram's syntax is always valid and it can't carry numbers
or results. Diagrams illustrate what the paper describes; they are never evidence."""
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from experiments.brief import json_object
from utils.llm import ainvoke_llm

MAX_DIAGRAMS = 2
MAX_NODES, MAX_EDGES = 12, 16
MAX_LABEL = 48
DIRECTIONS = {"LR", "TB"}
_UNSAFE = re.compile(r'["`<>{}\[\]|#;]')

PROMPT = """You plan the diagrams of a research paper: figures that make its system architecture, method
pipeline or taxonomy easier to follow. Propose at most {n}, and none if the paper doesn't need one. A diagram
shows only components and how they connect, as the paper describes them: no numbers, results or claims.
Labels are short (2-5 words). Use at most {nodes} boxes. Use direction "TB" (top to bottom) unless there are 4
boxes or fewer, so the diagram fits one column. Put each diagram in the section that explains it.

Return ONLY JSON: {{"diagrams": [{{"section": "one of the section titles, exactly", "caption": "one sentence",
"direction": "LR or TB", "nodes": [{{"id": "a", "label": "Short label"}}], "edges": [{{"from": "a", "to": "b",
"label": "optional, 1-3 words"}}]}}]}}"""


def _label(text, limit: int = MAX_LABEL) -> str:
    text = " ".join(_UNSAFE.sub(" ", str(text or "")).split())
    return text[:limit].rstrip()


def to_mermaid(diagram: dict) -> str | None:
    """Mermaid flowchart source for {"direction", "nodes", "edges"}, or None if there is nothing valid to draw.
    Node ids are renamed (n1, n2, ...), labels are quoted and stripped of Mermaid's special characters."""
    ids, lines = {}, []
    for node in (diagram.get("nodes") or [])[:MAX_NODES]:
        key, label = str((node or {}).get("id", "")).strip(), _label((node or {}).get("label"))
        if key and label and key not in ids:
            ids[key] = f"n{len(ids) + 1}"
            lines.append(f'    {ids[key]}["{label}"]')
    edges = []
    for edge in (diagram.get("edges") or [])[:MAX_EDGES]:
        a, b = ids.get(str((edge or {}).get("from", ""))), ids.get(str((edge or {}).get("to", "")))
        if a and b and a != b:
            label = _label(edge.get("label"), 24)
            edges.append(f'    {a} -->|"{label}"| {b}' if label else f"    {a} --> {b}")
    if len(ids) < 2 or not edges:
        return None
    direction = str(diagram.get("direction", "")).upper()
    direction = direction if direction in DIRECTIONS else ("LR" if len(ids) <= 4 else "TB")
    return "\n".join([f"flowchart {direction}", *lines, *edges])


def match_section(name: str, titles: list[str]) -> str | None:
    """The section title the model meant: exact, then ignoring case, then by containment."""
    name = str(name or "").strip().lower()
    if not name:
        return None
    lowered = [t.lower() for t in titles]
    if name in lowered:
        return titles[lowered.index(name)]
    return next((t for t, low in zip(titles, lowered) if name in low or low in name), None)


async def plan_diagrams(context: str, sections: list[dict]) -> list[dict]:
    """Diagrams for the paper, each placed in one of its sections. Any failure means no diagrams."""
    titles = [str(s.get("title", "")) for s in sections if s.get("title")]
    if not titles:
        return []
    outline = "\n".join(f"- {s.get('title')}: {s.get('description', '')}" for s in sections)
    messages = [SystemMessage(content=PROMPT.format(n=MAX_DIAGRAMS, nodes=MAX_NODES)),
                HumanMessage(content=f"Sections:\n{outline}\n\n{context}")]
    try:
        response = await ainvoke_llm(messages, agent_name="figure_planning", temperature=0.2)
    except Exception as e:
        print(f"Diagram planning skipped: {e}")
        return []
    planned = json_object(response.content).get("diagrams")
    diagrams = []
    for raw in planned if isinstance(planned, list) else []:
        source = to_mermaid(raw if isinstance(raw, dict) else {})
        section = match_section(raw.get("section"), titles) if isinstance(raw, dict) else None
        caption = _label(raw.get("caption"), 200) if isinstance(raw, dict) else ""
        if source and section and caption:
            nodes = [n.get("label") for n in raw.get("nodes", []) if isinstance(n, dict)]
            diagrams.append({"id": f"fig-diagram-{len(diagrams) + 1}", "kind": "diagram", "origin": "illustrative",
                             "mermaid": source, "caption": caption, "section": section,
                             "summary": "boxes: " + json.dumps([_label(n) for n in nodes][:MAX_NODES])})
        if len(diagrams) == MAX_DIAGRAMS:
            break
    return diagrams
