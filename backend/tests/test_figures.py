"""Paper figures: charts and tables from measured results, diagrams compiled from JSON, and the placement
pass that keeps the paper's structure valid whatever a model does to the markers."""
import asyncio
import json
from langchain_core.messages import AIMessage
import figures.diagrams
from figures import build_figures
from figures.charts import build_figures as from_scratch, improve_figures
from figures.diagrams import match_section, to_mermaid
from figures.placement import place_figures

BRIEF = {"objective": "o", "target": "t", "metric": {"name": "seconds", "goal": "minimize"}}
NOTEBOOK = [
    {"n": 1, "hypothesis": "baseline: the unmodified code", "metric": 0.34, "spread": 0.06, "checks": {}, "verdict": "baseline"},
    {"n": 2, "hypothesis": "use a sieve", "metric": 0.039, "spread": 0.002, "checks": {"tests": True}, "verdict": "improved"},
    {"n": 3, "hypothesis": "unroll the loop", "metric": None, "spread": 0, "checks": {"tests": False}, "verdict": "failed checks"},
]
FIGS = [{"id": "fig-a", "kind": "chart", "origin": "measured", "caption": "A", "section": "Results"},
        {"id": "tab-a", "kind": "table", "origin": "measured", "caption": "T", "section": "Results"}]
PAPER = """# Title

## Abstract

Short [1].

## Index Terms

a, b

## Method

We did things [2].

## Results

Speed improved [[REF:fig-a]] by 8.8x [3].

## Conclusion

Done.
"""


def body_of(paper: str, title: str) -> str:
    return paper.split(f"## {title}\n")[1].split("\n## ")[0]


# ---- Placement --------------------------------------------------------------------

def test_a_marker_the_model_dropped_goes_back_after_the_paragraph_that_refers_to_it():
    out = place_figures(PAPER, FIGS)
    results = body_of(out, "Results")
    assert results.index("[[REF:fig-a]]") < results.index("[[FIGURE:fig-a]]")
    assert out.count("[[FIGURE:fig-a]]") == 1 and out.count("[[FIGURE:tab-a]]") == 1
    assert "[[FIGURE:tab-a]]" in results  # unreferenced: the end of its own section


def test_structure_and_citations_survive_placement():
    out = place_figures(PAPER, FIGS)
    headings = [line for line in out.splitlines() if line.startswith("#")]
    assert headings == ["# Title", "## Abstract", "## Index Terms", "## Method", "## Results", "## Conclusion"]
    assert "Short [1]." in out and "We did things [2]." in out and "by 8.8x [3]." in out


def test_markers_never_stay_in_the_abstract_and_never_repeat():
    messy = PAPER.replace("Short [1].", "Short [1]. [[FIGURE:fig-a]]").replace("Done.", "Done.\n\n[[FIGURE:fig-a]]\n\n[[FIGURE:nope]]")
    out = place_figures(messy, FIGS)
    assert "[[FIGURE" not in body_of(out, "Abstract")
    assert out.count("[[FIGURE:fig-a]]") == 1 and "nope" not in out
    assert "\n[[FIGURE:fig-a]]\n" in body_of(out, "Conclusion") + "\n"  # the first body marker wins


def test_an_inline_marker_moves_to_its_own_line_after_its_paragraph():
    out = place_figures(PAPER.replace("We did things [2].", "We did [[FIGURE:fig-a]] things [2]."), FIGS)
    method = body_of(out, "Method")
    assert "We did things [2]." in method.replace("  ", " ") and method.strip().endswith("[[FIGURE:fig-a]]")


def test_references_to_unknown_figures_are_replaced():
    out = place_figures(PAPER.replace("[[REF:fig-a]]", "[[REF:fig-zzz]]"), FIGS)
    assert "fig-zzz" not in out and "the figure" in out


def test_placement_is_stable():
    once = place_figures(PAPER, FIGS)
    assert place_figures(once, FIGS) == once


# ---- Diagrams ---------------------------------------------------------------------

def test_diagrams_compile_to_valid_quoted_mermaid():
    source = to_mermaid({"direction": "TB", "nodes": [{"id": "a", "label": 'Loader "fast" [mmap]'}, {"id": "b", "label": "KV cache"},
                                                      {"id": "b", "label": "dup"}],
                         "edges": [{"from": "a", "to": "b", "label": "pages|in"}, {"from": "a", "to": "ghost"}]})
    assert source.splitlines() == ["flowchart TB", '    n1["Loader fast mmap"]', '    n2["KV cache"]', '    n1 -->|"pages in"| n2']
    assert to_mermaid({"nodes": [{"id": "a", "label": "x"}], "edges": []}) is None


def test_the_planned_section_is_matched_loosely():
    assert match_section("system architecture", ["Introduction", "System Architecture"]) == "System Architecture"
    assert match_section("Methods", ["Proposed Methods and Design"]) == "Proposed Methods and Design"
    assert match_section("Nowhere", ["Introduction"]) is None


def test_planned_diagrams_are_validated(monkeypatch):
    plan = {"diagrams": [
        {"section": "method", "caption": "The pipeline.", "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
         "edges": [{"from": "a", "to": "b"}]},
        {"section": "Nowhere", "caption": "Lost.", "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}], "edges": [{"from": "a", "to": "b"}]},
        {"section": "Method", "caption": "Empty.", "nodes": [], "edges": []},
    ]}
    async def fake(messages, agent_name=None, **kwargs):
        return AIMessage(content=json.dumps(plan))
    monkeypatch.setattr(figures.diagrams, "ainvoke_llm", fake)
    found = asyncio.run(figures.diagrams.plan_diagrams("ctx", [{"title": "Method"}, {"title": "Results"}]))
    assert [(d["id"], d["section"], d["origin"]) for d in found] == [("fig-diagram-1", "Method", "illustrative")]
    assert found[0]["mermaid"].startswith("flowchart LR")


# ---- Charts and tables --------------------------------------------------------------

def test_attempts_become_a_chart_and_a_table_with_failures_included():
    chart, table = improve_figures(NOTEBOOK, BRIEF, repeats=5)
    assert chart["svg"].lstrip().startswith("<?xml") and "<svg" in chart["svg"] and "Baseline" in chart["svg"]
    assert chart["summary"] == "Baseline: 0.34; #2: 0.039"  # #3 failed its checks: not plotted...
    rows = table["table"]["rows"]
    assert [r[0] for r in rows] == ["1", "2", "3"] and rows[2][2] == "—" and rows[2][4] == "failed checks"  # ...but listed
    assert rows[1][3] == "-88.5%"


def test_no_baseline_means_no_figures_and_zero_baseline_is_safe():
    assert improve_figures([{**NOTEBOOK[0], "metric": None}], BRIEF, 5) == []
    zero = [{**NOTEBOOK[0], "metric": 0.0}, NOTEBOOK[1]]
    assert improve_figures(zero, BRIEF, 5)[1]["table"]["rows"][1][3] == "—"


def test_from_scratch_results_group_by_metric():
    notebook = [{"n": 1, "verdict": "works", "results": {"quick.seconds": {"mean": 1.0, "spread": 0.1},
                                                          "merge.seconds": {"mean": 2.0, "spread": 0.2}}}]
    table, chart = from_scratch(notebook, repeats=3)
    assert table["table"]["columns"] == ["Variant", "seconds"]
    assert table["table"]["rows"] == [["merge", "2 ± 0.2"], ["quick", "1 ± 0.1"]]
    assert chart["id"] == "fig-results-1" and "quick" in chart["svg"]


def test_measured_figures_go_to_the_results_section():
    state = {"notebook": NOTEBOOK, "experiment_brief": BRIEF, "lab": {"spec": {"repeats": 5}}, "topic": "t"}
    sections = [{"title": "Introduction"}, {"title": "Experimental Evaluation"}, {"title": "Conclusion"}]
    found = asyncio.run(build_figures(state, sections))
    assert {f["id"]: f["section"] for f in found} == {"fig-attempts": "Experimental Evaluation", "tab-attempts": "Experimental Evaluation"}


def test_writer_and_editor_keep_every_figure_even_when_the_editor_drops_them(monkeypatch):
    import agents.writer, agents.refinement
    prompts = []
    async def writer_llm(messages, agent_name=None, **kwargs):
        prompts.append(messages[0].content)
        return AIMessage(content="Speed improved [[REF:fig-attempts]] [1]." if "Evaluation" in messages[0].content.split("\n")[1] else "Text [1].")
    async def editor_llm(messages, agent_name=None, **kwargs):  # rewrites everything and loses the markers
        return AIMessage(content="# T\n\n## Abstract\n\nA.\n\n## Introduction\n\nText [1].\n\n## Evaluation\n\nFaster, see [[REF:fig-attempts]] [1].\n")
    monkeypatch.setattr(agents.writer, "ainvoke_llm", writer_llm)
    monkeypatch.setattr(agents.refinement, "ainvoke_llm", editor_llm)
    monkeypatch.setattr(agents.writer, "section_evidence", lambda *a, **k: asyncio.sleep(0, result=[]))
    state = {"topic": "t", "notebook": NOTEBOOK, "experiment_brief": BRIEF, "lab": {"spec": {"repeats": 5}},
             "research_plan": {"sections": [{"title": "Introduction", "description": "i"}, {"title": "Evaluation", "description": "e"}]}}
    out = asyncio.run(agents.writer.writer_node(state))
    assert {f["id"] for f in out["figures"]} == {"fig-attempts", "tab-attempts"}
    assert "[[FIGURE:fig-attempts]]" in out["draft_report"] and "[[FIGURE:tab-attempts]]" in out["draft_report"]
    assert "[[FIGURE:fig-attempts]]" in next(p for p in prompts if "Write the 'Evaluation'" in p)
    final = asyncio.run(agents.refinement.refinement_node({**state, **out, "critic_feedback": "f"}))["final_report"]
    evaluation = final.split("## Evaluation\n")[1]
    assert evaluation.index("[[REF:fig-attempts]]") < evaluation.index("[[FIGURE:fig-attempts]]")
    assert final.count("[[FIGURE:fig-attempts]]") == 1 and "[[FIGURE:tab-attempts]]" in evaluation


def test_the_highlighted_bar_is_the_change_kept_not_a_gain_within_noise():
    noise = {"n": 4, "hypothesis": "tiny tweak", "metric": 0.038, "spread": 0.004, "checks": {"tests": True}, "verdict": "no gain"}
    chart = improve_figures(NOTEBOOK + [noise], BRIEF, 5)[0]
    assert chart["svg"].count("#ff511c") == 1 and "the highlighted bar is the change kept" in chart["caption"]
    nothing_kept = improve_figures([NOTEBOOK[0], {**noise, "n": 2}], BRIEF, 5)[0]
    assert "#ff511c" not in nothing_kept["svg"] and "no change beat the baseline" in nothing_kept["caption"]


def test_diagrams_with_many_boxes_run_top_to_bottom_to_fit_a_column():
    many = {"nodes": [{"id": str(i), "label": f"Box {i}"} for i in range(5)], "edges": [{"from": "0", "to": "1"}]}
    assert to_mermaid(many).startswith("flowchart TB")
    assert to_mermaid({**many, "nodes": many["nodes"][:3]}).startswith("flowchart LR")
