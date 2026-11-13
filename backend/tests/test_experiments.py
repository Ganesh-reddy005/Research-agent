"""The experiment brief and the fork between writing the draft and running experiments first."""
import asyncio
import pytest
from experiments.brief import normalise_brief, missing_fields, MAX_ATTEMPTS, DEFAULT_ATTEMPTS
from test_api import client, start, THREAD, CONFIG  # noqa: F401  (client is a fixture)

def test_brief_is_normalised_whatever_the_model_sends():
    brief = normalise_brief({"objective": "  Speed  up\n inference ", "metric": {"name": "latency", "goal": "lower"},
                             "must_hold": "tests pass", "off_limits": ["", "the dataset"] + ["x"] * 20,
                             "attempt_limit": 999}, default_target="https://github.com/o/r")
    assert brief["objective"] == "Speed up inference"
    assert brief["target"] == "https://github.com/o/r"  # the project's repository when the model gave none
    assert brief["metric"]["goal"] == "maximize"  # unknown goals fall back rather than fail
    assert brief["must_hold"] == ["tests pass"]  # a single string becomes a list
    assert brief["off_limits"][0] == "the dataset" and len(brief["off_limits"]) == 12
    assert brief["attempt_limit"] == MAX_ATTEMPTS
    assert normalise_brief("not a dict")["attempt_limit"] == DEFAULT_ATTEMPTS

def test_brief_lists_what_is_missing_before_the_agent_can_start():
    empty = normalise_brief({})
    assert missing_fields(empty) == ["objective", "metric"]  # no target: Lume finds or writes the code
    ready = normalise_brief({"objective": "o", "target": "t", "metric": {"name": "m"}})
    assert missing_fields(ready) == []
    assert missing_fields({**ready, "open_questions": ["Which dataset?"]}) == ["answers to the open questions"]

class NoDatabase:
    """Marking a session completed in Supabase isn't under test here."""
    def table(self, name): return self
    def update(self, *a): return self
    def eq(self, *a): return self
    def execute(self): return None

@pytest.fixture(autouse=True)
def no_database(monkeypatch):
    from api.routers import research
    monkeypatch.setattr(research, "get_supabase_client", NoDatabase)

def resume(http, action, data=None):
    with http.stream("POST", "/api/research/resume", json={"thread_id": THREAD, "action": action, "data": data or {}}) as res:
        assert res.status_code == 200
        return "".join(res.iter_text())

def test_planning_experiments_drafts_a_brief_and_pauses_on_it(client):
    http, graph = client
    start(graph, pauses=3)  # paused after assistance, at the review

    body = resume(http, "plan_experiments")

    assert '"step": "experiment_brief"' in body  # the interrupt says which pause this is
    snapshot = asyncio.run(graph.aget_state(CONFIG))
    assert snapshot.next == ("synthesis",)
    brief = snapshot.values["experiment_brief"]
    assert brief["metric"] == {"name": "tokens per second", "goal": "maximize", "measured_by": ""}
    assert brief["must_hold"] == ["unit tests pass"]
    assert "draft_report" not in snapshot.values  # nothing written yet

def test_edited_brief_is_saved_and_writing_the_draft_still_works(client):
    http, graph = client
    start(graph, pauses=3)
    resume(http, "plan_experiments")

    res = http.put(f"/api/research/{THREAD}/brief", json={"brief": {"objective": "Edited", "metric": {"name": "m"}}})
    assert res.status_code == 200
    assert res.json()["missing"] == []
    assert asyncio.run(graph.aget_state(CONFIG)).values["experiment_brief"]["objective"] == "Edited"

    assert "event: done" in resume(http, "continue")  # "Write the draft instead"
    assert asyncio.run(graph.aget_state(CONFIG)).values["final_report"]

def test_review_without_experiments_writes_the_draft_directly(client):
    http, graph = client
    start(graph, pauses=3)
    assert "event: done" in resume(http, "continue")
    assert "experiment_brief" not in asyncio.run(graph.aget_state(CONFIG)).values

def test_brief_cannot_be_saved_unless_the_session_is_paused_on_it(client):
    http, graph = client
    start(graph, pauses=3)  # at the review, no brief yet
    res = http.put(f"/api/research/{THREAD}/brief", json={"brief": {"objective": "x"}})
    assert res.status_code == 409
