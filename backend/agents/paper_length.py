"""How long the paper should be, as agents see it.

The user can ask for a number of IEEE pages. Every length rule (how many sections the planner
makes, how much the writer writes per section, how much the editor may output) comes from here.
Without a target, the defaults give the original short paper of about 2 pages."""

MAX_PAGES = 15
# Words of text on a two-column IEEE page, allowing for the title, headings and references
WORDS_PER_PAGE = 800
ABSTRACT_WORDS = 180


def target_pages(state) -> int | None:
    pages = state.get("target_pages")
    return pages if isinstance(pages, int) and pages > 0 else None


def target_words(state) -> int | None:
    pages = target_pages(state)
    return pages * WORDS_PER_PAGE if pages else None


def section_range(state) -> tuple[int, int]:
    """How many sections the plan should have: longer papers get more, not just longer, sections."""
    pages = target_pages(state)
    if not pages or pages <= 2:
        return (4, 5) if pages else (5, 6)
    if pages <= 4:
        return (5, 6)
    if pages <= 8:
        return (6, 8)
    return (8, 10)


def planning_rule(state) -> str:
    low, high = section_range(state)
    pages = target_pages(state)
    length = f" The paper must fill about {pages} IEEE pages (~{target_words(state):,} words)." if pages else ""
    subsections = " Long sections may list 2-3 subsection questions each." if pages and pages > 8 else ""
    return f"Target {low}-{high} sections for the paper (Introduction, body sections, Conclusion).{length}{subsections}"


def section_words(state, section_count: int) -> tuple[int, int]:
    """Word range for one section, so all sections together reach the target length."""
    words = target_words(state)
    if not words:
        return 150, 250
    per_section = max(120, (words - ABSTRACT_WORDS) // max(section_count, 1))
    # Writers overshoot long targets by about 30% (a 6-page test run drafted 5,956 words for 4,800),
    # so the range sits below the even share
    return int(per_section * 0.75), int(per_section * 1.0)


def writer_rule(state, section_count: int) -> str:
    low, high = section_words(state, section_count)
    rule = f"Target {low}-{high} words for this section."
    if high > 600:
        rule += " Use '### ' subsection headings to structure it, and keep paragraphs focused."
    else:
        rule += " Be concise but rigorous. Never produce very large blocks of text."
    return rule


def evidence_size(state, section_count: int) -> int:
    """Literature passages per section: a longer section needs more to draw on."""
    _, high = section_words(state, section_count)
    return min(16, max(8, high // 50))


def editing_rule(state) -> str:
    words = target_words(state)
    if not words:
        return "Prune redundant sentences and fluff. Aim for a high-density, concise academic style (150-250 words per section)."
    return (f"The paper must stay about {words:,} words long (~{target_pages(state)} IEEE pages). "
            "Keep each section's length and depth; prune only repetition and fluff, never content.")


def editing_max_tokens(state) -> int:
    """The editor rewrites the whole paper in one call: leave room for all of it."""
    words = target_words(state) or 0
    return max(8000, int(words * 1.8))
