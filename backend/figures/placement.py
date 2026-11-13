"""Where figures go in the paper, enforced in code so no model can break the structure.

The writer marks a figure with a line [[FIGURE:id]] and refers to it with [[REF:id]] (shown as "Fig. 1" or
"Table I"). After any model has written or rewritten the paper, place_figures makes it valid again: every
known figure appears exactly once, on its own line, inside a body section (never in the title, abstract,
index terms or references); unknown or repeated markers are dropped; a figure the text lost is put back
after the paragraph that refers to it, or at the end of the section it belongs to."""
import re

MARKER = re.compile(r"\[\[FIGURE:([A-Za-z0-9_-]+)\]\]")
REF = re.compile(r"\[\[REF:([A-Za-z0-9_-]+)\]\]")
HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*#*\s*$")
NOT_BODY = re.compile(r"^(abstract|index terms|keywords|references|bibliography|works cited|sources)$", re.I)
RESULTS_WORDS = ("result", "evaluation", "experiment", "finding", "benchmark", "performance", "discussion")
CLOSING_WORDS = ("conclusion", "future work", "summary")


def marker(fig_id: str) -> str:
    return f"[[FIGURE:{fig_id}]]"


def home_section(figure: dict, titles: list[str]) -> str | None:
    """The body section a figure belongs in: its own, else (measured results) the results section,
    else the last section before the conclusion."""
    lowered = [t.lower() for t in titles]
    wanted = str(figure.get("section") or "").lower()
    if wanted in lowered:
        return titles[lowered.index(wanted)]
    if figure.get("origin") == "measured":
        found = next((t for t, low in zip(titles, lowered) if any(w in low for w in RESULTS_WORDS)), None)
        if found:
            return found
    body = [t for t, low in zip(titles, lowered) if not any(w in low for w in CLOSING_WORDS)]
    return (body or titles)[-1] if titles else None


def _sections(markdown: str) -> list[dict]:
    """[{heading, title, body: [blocks]}]: the text before the first ## is a section with no title."""
    sections = [{"heading": None, "title": "", "blocks": []}]
    block: list[str] = []
    def flush():
        if block:
            sections[-1]["blocks"].append("\n".join(block).strip("\n"))
            block.clear()
    for line in markdown.replace("\r", "").split("\n"):
        heading = HEADING.match(line)
        if heading and len(heading.group(1)) >= 2:
            flush()
            sections.append({"heading": line, "title": heading.group(2).strip(), "blocks": []})
        elif MARKER.fullmatch(line.strip()) or not line.strip():
            flush()
            if line.strip():
                sections[-1]["blocks"].append(line.strip())
        else:
            block.append(line)
    flush()
    return sections


def place_figures(markdown: str, figures: list[dict]) -> str:
    known = {f["id"]: f for f in figures}
    if not known and not MARKER.search(markdown) and not REF.search(markdown):
        return markdown  # nothing to place: the text stays exactly as written
    sections = _sections(markdown)
    body = [s for s in sections if s["heading"] and not NOT_BODY.match(s["title"])]
    placed: set[str] = set()
    for section in sections:
        blocks = []
        for block in section["blocks"]:
            ids = MARKER.findall(block)
            text = MARKER.sub("", block).strip() if ids else block
            if text:
                blocks.append(text)
            for fig_id in ids:  # a marker inside a paragraph goes on its own line after it
                if fig_id in known and fig_id not in placed and section in body:
                    blocks.append(marker(fig_id))
                    placed.add(fig_id)
        section["blocks"] = blocks
    titles = [s["title"] for s in body]
    for fig_id, figure in known.items():
        if fig_id in placed or not body:
            continue
        referring = next(((s, i) for s in body for i, b in enumerate(s["blocks"]) if f"[[REF:{fig_id}]]" in b), None)
        if referring:
            section, i = referring
            section["blocks"].insert(i + 1, marker(fig_id))
        else:
            home = home_section(figure, titles)
            next(s for s in body if s["title"] == home)["blocks"].append(marker(fig_id))
        placed.add(fig_id)
    out = []
    for section in sections:
        if section["heading"]:
            out.append(section["heading"])
        out.extend(REF.sub(lambda m: m.group(0) if m.group(1) in known else "the figure", b) for b in section["blocks"])
    return "\n\n".join(part for part in out if part.strip()).strip() + "\n"


def figure_notes(figures: list[dict], section_title: str) -> str:
    """The figures a section's writer should place and discuss, for its prompt."""
    mine = [f for f in figures if f.get("section") == section_title]
    if not mine:
        return ""
    lines = []
    for f in mine:
        kind = "table" if f["kind"] == "table" else "figure"
        detail = f.get("summary") or ""
        if f["kind"] == "table":
            detail = "columns: " + ", ".join(f["table"]["columns"])
        lines.append(f"- {marker(f['id'])} ({kind}, {f['origin']}): {f['caption']} {detail}".rstrip())
    return ("FIGURES AND TABLES FOR THIS SECTION (made by the system from the paper's data; never invent others):\n"
            + "\n".join(lines) + "\nPut each marker, exactly as written, on its own line right after the paragraph "
            "that first discusses it, and refer to it in the text as [[REF:<id>]] (it becomes \"Fig. 1\" or "
            "\"Table I\"). Use each marker once. Don't draw tables or images yourself.\n")
