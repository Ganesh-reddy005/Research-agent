import asyncio
import pytest
from langchain_core.messages import AIMessage

import agents.planning, agents.writer, agents.refinement
from agents import paper_length
from api.models import ResearchStartRequest
from api.routers import research
from conftest import PLAN

def test_default_length_is_the_original_short_paper():
    state = {}
    assert paper_length.section_range(state) == (5, 6)
    assert paper_length.section_words(state, 6) == (150, 250)
    assert paper_length.editing_max_tokens(state) == 8000
    assert paper_length.evidence_size(state, 6) == 8

@pytest.mark.parametrize("pages", [1, 2, 4, 6, 10, 15])
def test_sections_add_up_to_the_requested_pages(pages):
    state = {"target_pages": pages}
    low, high = paper_length.section_range(state)
    for sections in (low, high):
        lo, hi = paper_length.section_words(state, sections)
        total = paper_length.ABSTRACT_WORDS + (lo + hi) / 2 * sections
        assert abs(total - pages * paper_length.WORDS_PER_PAGE) <= 0.2 * pages * paper_length.WORDS_PER_PAGE + 150
    assert paper_length.editing_max_tokens(state) >= pages * paper_length.WORDS_PER_PAGE * 1.5

def test_longer_papers_get_more_sections_and_evidence():
    short, long = {"target_pages": 2}, {"target_pages": 12}
    assert paper_length.section_range(long)[0] > paper_length.section_range(short)[1]
    assert paper_length.evidence_size(long, 9) > paper_length.evidence_size(short, 5)
    assert "###" in paper_length.writer_rule(long, 9)

def capture_prompts(monkeypatch, module, reply):
    prompts = []
    async def fake(messages, **kwargs):
        prompts.append((messages[0].content, kwargs))
        return AIMessage(content=reply)
    monkeypatch.setattr(module, "ainvoke_llm", fake)
    return prompts

def test_requested_pages_reach_planner_writer_and_editor(monkeypatch):
    import json
    state = {"topic": "t", "target_pages": 10, "research_plan": PLAN["research_plan"], "raw_sources": []}

    planner = capture_prompts(monkeypatch, agents.planning, json.dumps(PLAN))
    asyncio.run(agents.planning.planning_node(state))
    assert "8-10 sections" in planner[0][0] and "about 10 IEEE pages" in planner[0][0]

    writer = capture_prompts(monkeypatch, agents.writer, "Body.")
    asyncio.run(agents.writer.writer_node(state))
    low, high = paper_length.section_words(state, 1)
    assert f"Target {low}-{high} words" in writer[0][0]

    editor = capture_prompts(monkeypatch, agents.refinement, "Paper.")
    asyncio.run(agents.refinement.refinement_node({**state, "draft_report": "d", "critic_feedback": "f"}))
    assert "8,000 words" in editor[0][0] and "never content" in editor[0][0]
    assert editor[0][1]["max_tokens"] == paper_length.editing_max_tokens(state)

def test_start_request_carries_pages_for_both_paper_modes():
    state, _ = research.initial_state(ResearchStartRequest(topic="t", pages=6))
    assert state["target_pages"] == 6
    state, _ = research.initial_state(ResearchStartRequest(repo_url="octo/sparse", pages=3))
    assert state["target_pages"] == 3
    state, _ = research.initial_state(ResearchStartRequest(topic="t"))
    assert "target_pages" not in state

@pytest.mark.parametrize("pages", [0, paper_length.MAX_PAGES + 1])
def test_out_of_range_pages_are_rejected(pages):
    with pytest.raises(ValueError):
        ResearchStartRequest(topic="t", pages=pages)
