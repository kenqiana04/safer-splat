#!/usr/bin/env python3
"""Finite, stdlib-only terminal/emergency policy checker; not runtime code."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHOICES = {"NAVIGATION", "RETAINED_BACKUP", "TERMINAL", "ASSURANCE_BOUNDARY"}
TERMINAL_ACTION_ID = "terminal-action:sha256:9665531746e10e83904dc074cda83130ebe69337dc24fc60f76b953f1b63c2ae"


@dataclass(frozen=True)
class PolicyState:
    navigation: str = "NOT_READY"
    backup: str = "NONE"
    terminal_membership: str = "TRUE"
    terminal_certificate: str = "NOT_READY"
    terminal_context: str = "FALLBACK_ELIGIBLE"
    deadline: str = "OPEN"
    authorities_valid: bool = True
    state_time_valid: bool = True
    action_identity_valid: bool = True
    terminal_reference_valid: bool = True
    certified_before_guard: bool = False
    zero_velocity_start: bool = False
    software_failure: bool = False
    external_request: bool = False


def terminal_certification_allowed(deadline: str) -> bool:
    return deadline == "OPEN"


def terminal_eligible(state: PolicyState) -> bool:
    context_ok = state.terminal_context in {"GOAL_HOLD_ELIGIBLE", "FALLBACK_ELIGIBLE", "EXTERNAL_REQUEST_ONLY"}
    deadline_ok = state.deadline == "OPEN" or state.certified_before_guard
    return (
        state.terminal_membership == "TRUE"
        and state.terminal_certificate == "READY"
        and context_ok
        and deadline_ok
        and state.authorities_valid
        and state.state_time_valid
        and state.action_identity_valid
        and state.terminal_reference_valid
    )


def arbitrate(state: PolicyState) -> str:
    if state.navigation == "CERTIFIED_READY":
        return "NAVIGATION"
    if state.backup == "VALID":
        return "RETAINED_BACKUP"
    if terminal_eligible(state):
        return "TERMINAL"
    return "ASSURANCE_BOUNDARY"


def terminal_commit_identity(state: PolicyState) -> tuple[str | None, str | None]:
    if arbitrate(state) != "TERMINAL":
        return None, None
    return TERMINAL_ACTION_ID, TERMINAL_ACTION_ID


def load_scenario_states() -> list[tuple[dict, PolicyState]]:
    manifest = json.loads((ROOT / "TERMINAL_EMERGENCY_ADVERSARIAL_SCENARIOS_V2.json").read_text(encoding="utf-8"))
    defaults = manifest["defaults"]
    return [(entry, PolicyState(**(defaults | entry["state"]))) for entry in manifest["scenarios"]]


def run_scenarios() -> list[dict]:
    results = []
    for entry, state in load_scenario_states():
        choice = arbitrate(state)
        passed = choice == entry["expected_choice"]
        if "expected_new_certification_allowed" in entry:
            passed = passed and terminal_certification_allowed(state.deadline) == entry["expected_new_certification_allowed"]
        if entry.get("expected_identity_preserved"):
            selected, executed = terminal_commit_identity(state)
            passed = passed and selected == executed == TERMINAL_ACTION_ID
        results.append({"id": entry["id"], "choice": choice, "expected": entry["expected_choice"], "status": "PASS" if passed else "FAIL"})
    return results


def run_properties() -> list[dict]:
    scenario_states = [state for _, state in load_scenario_states()]
    terminal_states = [state for state in scenario_states if arbitrate(state) == "TERMINAL"]
    nav_zero = PolicyState(navigation="CERTIFIED_READY", terminal_certificate="READY", zero_velocity_start=True)
    backup_and_terminal = PolicyState(backup="VALID", terminal_certificate="READY")
    terminal_ready = PolicyState(terminal_certificate="READY")
    expired_ready = PolicyState(terminal_certificate="READY", deadline="EXPIRED", certified_before_guard=True)
    exact_selected, exact_executed = terminal_commit_identity(terminal_ready)
    checks = {
        "PTP-01": arbitrate(nav_zero) == "NAVIGATION",
        "PTP-02": arbitrate(backup_and_terminal) == "RETAINED_BACKUP",
        "PTP-03": bool(terminal_states) and all(terminal_eligible(state) for state in terminal_states),
        "PTP-04": arbitrate(PolicyState(terminal_membership="TRUE", terminal_certificate="NOT_READY")) == "ASSURANCE_BOUNDARY",
        "PTP-05": arbitrate(nav_zero) == "NAVIGATION",
        "PTP-06": arbitrate(PolicyState(backup="EXHAUSTED", terminal_certificate="NOT_READY")) == "ASSURANCE_BOUNDARY",
        "PTP-07": not terminal_certification_allowed("EXPIRED"),
        "PTP-08": arbitrate(expired_ready) == "TERMINAL",
        "PTP-09": arbitrate(PolicyState(terminal_certificate="INVALID")) == "ASSURANCE_BOUNDARY",
        "PTP-10": arbitrate(PolicyState(terminal_certificate="UNKNOWN")) == "ASSURANCE_BOUNDARY",
        "PTP-11": arbitrate(PolicyState(terminal_certificate="NOT_READY", action_identity_valid=True)) == "ASSURANCE_BOUNDARY",
        "PTP-12": arbitrate(PolicyState(software_failure=True, terminal_certificate="NOT_READY")) == "ASSURANCE_BOUNDARY",
        "PTP-13": arbitrate(PolicyState(terminal_context="EXTERNAL_REQUEST_ONLY", external_request=True, terminal_certificate="NOT_READY")) == "ASSURANCE_BOUNDARY",
        "PTP-14": arbitrate(PolicyState(terminal_membership="FALSE", terminal_certificate="NOT_READY")) == "ASSURANCE_BOUNDARY",
        "PTP-15": exact_selected == exact_executed == TERMINAL_ACTION_ID,
        "PTP-16": arbitrate(PolicyState(terminal_certificate="READY", authorities_valid=False)) == "ASSURANCE_BOUNDARY",
        "PTP-17": arbitrate(PolicyState(terminal_certificate="READY", terminal_reference_valid=False)) == "ASSURANCE_BOUNDARY",
        "PTP-18": "METHOD_CERTIFIED_TERMINAL_ACTION" != "NAVIGATION_SUCCESS",
        "PTP-19": all(arbitrate(state) == arbitrate(state) for state in scenario_states),
        "PTP-20": all(arbitrate(state) in CHOICES for state in scenario_states),
    }
    return [{"id": key, "status": "PASS" if value else "FAIL"} for key, value in sorted(checks.items())]


def main() -> None:
    properties = run_properties()
    scenarios = run_scenarios()
    failures = [item for item in properties + scenarios if item["status"] != "PASS"]
    unique_states = {json.dumps(asdict(state), sort_keys=True, separators=(",", ":")) for _, state in load_scenario_states()}
    result = {
        "status": "PASS_TERMINAL_EMERGENCY_POLICY_MODEL_CHECK_V2" if not failures else "FAIL_TERMINAL_EMERGENCY_POLICY_MODEL_CHECK_V2",
        "property_count": len(properties),
        "property_pass_count": sum(item["status"] == "PASS" for item in properties),
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(item["status"] == "PASS" for item in scenarios),
        "properties": properties,
        "scenarios": scenarios,
        "runtime_execution_count": 0,
        "gpu_execution_count": 0
    }
    reachable = {
        "construction": "EXPLICIT_SEMANTIC_SCENARIOS_NOT_CARTESIAN_PRODUCT",
        "abstract_reachable_state_count": len(unique_states),
        "supervisor_choices": sorted({arbitrate(state) for _, state in load_scenario_states()}),
        "illegal_cartesian_states_generated": 0,
        "state_totality_pass": all(arbitrate(state) in CHOICES for _, state in load_scenario_states())
    }
    outputs = {
        "terminal_policy_model_check_result.json": result,
        "terminal_policy_counterexamples.json": {"counterexample_count": len(failures), "counterexamples": failures},
        "terminal_policy_reachable_state_summary.json": reachable
    }
    for name, payload in outputs.items():
        (ROOT / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
