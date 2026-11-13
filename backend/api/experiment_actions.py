"""The user's decisions in the coding agent's loop, checked and turned into state updates:
launch from the brief, approve (or edit) the plan, and decide after each attempt's report."""
from fastapi import HTTPException
from experiments.brief import missing_fields, normalise_brief
from experiments.lab import DONE, clone_source, normalise_hypotheses, normalise_spec
from agents.experiment_loop import CONTINUE, REVISE, STOP

ACTIONS = {"launch_experiments", "approve_experiment_plan", "experiment_decision"}


def _launch(values: dict) -> dict:
    brief = normalise_brief(values.get("experiment_brief"), default_target=values.get("repo_url", ""))
    missing = missing_fields(brief)
    if missing:
        raise HTTPException(status_code=400, detail=f"Before launch, add: {', '.join(missing)}")
    if not clone_source(brief["target"]):
        raise HTTPException(status_code=400, detail="The target must be a repository URL (or a local git folder)")
    return {"experiment_brief": brief, "launch_experiments": True}


def _approve(values: dict, data: dict) -> dict:
    lab = values.get("lab") or {}
    done = [h for h in lab.get("hypotheses", []) if h.get("status") == DONE]
    hypotheses = normalise_hypotheses(data.get("hypotheses", lab.get("hypotheses")), done) if "hypotheses" in data \
        else lab.get("hypotheses", [])
    updated = {**lab, "hypotheses": hypotheses, "approved": True}
    if not lab.get("ready"):  # the benchmark is fixed once the baseline is measured
        updated["setup"] = [str(c) for c in data.get("setup", lab.get("setup", [])) if str(c).strip()]
        updated["spec"] = normalise_spec(data.get("spec", lab.get("spec")))
        if not updated["spec"]["measure"]:
            raise HTTPException(status_code=400, detail="The benchmark needs a measure command")
    if lab.get("ready") and not any(h["status"] != DONE for h in hypotheses):
        raise HTTPException(status_code=400, detail="Add at least one idea to try")
    return {"lab": updated}


def _decide(data: dict) -> dict:
    decision = data.get("decision")
    if decision not in {CONTINUE, REVISE, STOP}:
        raise HTTPException(status_code=400, detail="Decide to continue, change plan or stop")
    direction = str(data.get("direction", "")).strip()
    if decision == REVISE and not direction:
        raise HTTPException(status_code=400, detail="Say how the plan should change")
    return {"experiment_decision": {"decision": decision, "direction": direction}}


def experiment_update(action: str, values: dict, data: dict) -> dict:
    """The state update for one of the coding agent's actions; raises 400 when it isn't valid now."""
    step = values.get("current_step")
    expected = {"launch_experiments": "experiment_brief", "approve_experiment_plan": "exp_plan",
                "experiment_decision": "exp_reflect"}[action]
    if step != expected:
        raise HTTPException(status_code=409, detail="The session isn't waiting for that decision")
    if action == "launch_experiments":
        return _launch(values)
    return _approve(values, data) if action == "approve_experiment_plan" else _decide(data)
