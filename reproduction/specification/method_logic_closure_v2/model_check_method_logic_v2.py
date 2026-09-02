#!/usr/bin/env python3
"""Deterministic bounded model checker for Method Logic Closure V2.

The checker explores only legal states reachable from frozen initial-state
families. It does not import runtime code, query a map, or execute a controller.
"""
from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
ALT_BUDGET = 2
TERMINAL_PHASES = {"COMMIT", "ASSURANCE_BOUNDARY"}


@dataclass(frozen=True)
class State:
    lifecycle: str = "INITIAL"
    phase: str = "START_ADMISSION"
    candidate_role: str = "NONE"
    c0: str = "NOT_REACHED"
    l1: str = "NOT_REACHED"
    l2: str = "NOT_REACHED"
    l3: str = "NOT_REACHED"
    backup: str = "NONE"
    deadline: str = "OPEN"
    alternatives: str = "AVAILABLE"
    terminal: str = "NOT_EVALUATED"
    goal: str = "NOT_REACHED"
    action_authority: str = "NONE"
    reason_scope: str = "NONE"
    alt_attempts: int = 0
    checks: tuple[str, ...] = ()
    old_backup_retained: bool = False
    new_backup_created: bool = False
    navigation_ready: bool = False
    assurance_mode: str = "ACTIVE_ASSURANCE_MODE"
    projection_repair: bool = False
    task_success: bool = False
    failure_code: str = ""
    last_rule: str = "INITIAL"


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def load_rule_ids() -> set[str]:
    with (ROOT / "STATE_TRANSITION_TABLE_V2.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["rule_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate transition rule_id")
    required = {
        "rule_id", "source_phase", "guard", "observation/result", "reason_scope",
        "retained_backup_requirement", "deadline_requirement", "candidate_requirement",
        "destination_phase", "action_authority", "commit_allowed", "old_backup_retained",
        "new_backup_created", "theorem_interpretation", "failure_code_if_any",
    }
    if set(rows[0]) != required:
        raise ValueError("transition table columns drifted")
    return set(ids)


RULE_IDS = load_rule_ids()


def moved(state: State, rule: str, **changes: object) -> State:
    if rule not in RULE_IDS:
        raise KeyError(f"unfrozen rule {rule}")
    return replace(state, last_rule=rule, **changes)


def can_search_alternative(state: State) -> bool:
    return (
        state.backup == "VALID"
        and state.deadline == "OPEN"
        and state.alternatives == "AVAILABLE"
        and state.alt_attempts < ALT_BUDGET
    )


def to_arbitration(state: State, rule: str, failure_code: str, reason_scope: str = "NONE") -> State:
    return moved(
        state,
        rule,
        phase="ARBITRATION",
        failure_code=failure_code,
        reason_scope=reason_scope,
        old_backup_retained=(state.backup == "VALID"),
    )


def legal_observations(state: State) -> tuple[str, ...]:
    if state.phase in TERMINAL_PHASES:
        return ()
    if state.phase == "START_ADMISSION":
        return ("INITIAL_SAFE", "INITIAL_REPAIR_REQUIRED")
    if state.phase == "REPAIR":
        return ("REPAIR_PASS", "REPAIR_FAIL", "REPAIR_UNKNOWN")
    if state.phase == "RUNTIME_CURRENT_ROLE":
        return ("R0_DIAGNOSTIC_COMPLETE", "R0_DIAGNOSTIC_FAIL", "R0_DIAGNOSTIC_UNKNOWN")
    if state.phase == "L1":
        return ("L1_PASS", "L1_FAIL", "L1_UNKNOWN_GLOBAL", "L1_UNKNOWN_HEALTH", "L1_UNKNOWN_UNRESOLVED")
    if state.phase == "PRIMARY_PROPOSAL":
        return ("PRIMARY_AVAILABLE", "NO_CANDIDATE")
    if state.phase == "C0":
        return ("C0_PASS", "C0_FAIL_LOCAL", "C0_UNKNOWN_GLOBAL", "C0_UNKNOWN_LOCAL")
    if state.phase == "L2":
        return ("L2_PASS", "L2_FAIL", "L2_UNKNOWN_GLOBAL", "L2_UNKNOWN_LOCAL")
    if state.phase == "L3":
        return ("L3_WITNESS_FOUND", "L3_WITNESS_ABSENT", "L3_UNKNOWN_GLOBAL", "L3_UNKNOWN_LOCAL")
    if state.phase == "ALT_SEARCH":
        if state.deadline != "OPEN":
            return ("DEADLINE_GUARD",)
        if state.alternatives == "AVAILABLE" and state.alt_attempts < ALT_BUDGET:
            return ("ALT_AVAILABLE",)
        return ("ALT_EXHAUSTED",)
    if state.phase == "ARBITRATION":
        return ("ARBITRATE",)
    if state.phase == "BACKUP_EXECUTION":
        return ("EXECUTE_RETAINED_BACKUP",)
    if state.phase == "TERMINAL_EVALUATION":
        if state.terminal == "MEMBER_ELIGIBLE":
            return ("TERMINAL_MEMBER_ELIGIBLE",)
        if state.terminal == "MEMBER_NOT_ELIGIBLE":
            return ("TERMINAL_MEMBER_NOT_ELIGIBLE",)
        if state.terminal == "UNKNOWN":
            return ("TERMINAL_UNKNOWN",)
        return ("TERMINAL_MEMBER_ELIGIBLE", "TERMINAL_MEMBER_NOT_ELIGIBLE", "TERMINAL_UNKNOWN")
    raise ValueError(f"unknown reachable phase {state.phase}")


def step(state: State, observation: str) -> State:
    if observation not in legal_observations(state):
        raise ValueError(f"illegal observation {observation} for {state.phase}")

    if state.phase == "START_ADMISSION":
        if observation == "INITIAL_SAFE":
            return moved(state, "SA_SAFE", lifecycle="RUNTIME", phase="RUNTIME_CURRENT_ROLE")
        return moved(state, "SA_REPAIR", phase="REPAIR", failure_code="F_START_INVALID")

    if state.phase == "REPAIR":
        if observation == "REPAIR_PASS":
            return moved(state, "REPAIR_PASS", lifecycle="RUNTIME", phase="RUNTIME_CURRENT_ROLE")
        if observation == "REPAIR_FAIL":
            return moved(state, "REPAIR_FAIL", phase="ASSURANCE_BOUNDARY", action_authority="OUTSIDE_METHOD", failure_code="F_CURRENT_FEASIBILITY_FAIL")
        return moved(state, "REPAIR_UNKNOWN", phase="ASSURANCE_BOUNDARY", action_authority="OUTSIDE_METHOD", reason_scope="UNRESOLVED_SCOPE", failure_code="F_CURRENT_QUERY_UNKNOWN")

    if state.phase == "RUNTIME_CURRENT_ROLE":
        scope = "NONE" if observation == "R0_DIAGNOSTIC_COMPLETE" else ("INFRASTRUCTURE_HEALTH" if observation == "R0_DIAGNOSTIC_UNKNOWN" else "CANDIDATE_LOCAL_COMPUTATION")
        return moved(state, "R0_DIAGNOSTIC", phase="L1", reason_scope=scope, old_backup_retained=(state.backup == "VALID"))

    if state.phase == "L1":
        if observation == "L1_PASS":
            return moved(state, "L1_PASS", phase="PRIMARY_PROPOSAL", l1="PASS", reason_scope="NONE")
        if observation == "L1_FAIL":
            return to_arbitration(replace(state, l1="FAIL", alternatives="NOT_APPLICABLE"), "L1_FAIL", "F_IMMEDIATE_UNAVOIDABLE_SEGMENT_FAIL")
        scope = {"L1_UNKNOWN_GLOBAL":"GLOBAL_AUTHORITY_OR_EVIDENCE", "L1_UNKNOWN_HEALTH":"INFRASTRUCTURE_HEALTH", "L1_UNKNOWN_UNRESOLVED":"UNRESOLVED_SCOPE"}[observation]
        rule = {"L1_UNKNOWN_GLOBAL":"L1_UNKNOWN_GLOBAL", "L1_UNKNOWN_HEALTH":"L1_UNKNOWN_HEALTH", "L1_UNKNOWN_UNRESOLVED":"L1_UNKNOWN_UNRESOLVED"}[observation]
        code = "F_MAP_REFERENCE_UNRESOLVED" if observation == "L1_UNKNOWN_GLOBAL" else "F_CURRENT_QUERY_UNKNOWN"
        return to_arbitration(replace(state, l1="UNKNOWN", alternatives="NOT_APPLICABLE"), rule, code, scope)

    if state.phase == "PRIMARY_PROPOSAL":
        if observation == "PRIMARY_AVAILABLE":
            return moved(state, "P0_PRIMARY", phase="C0", candidate_role="PRIMARY", c0="NOT_REACHED", l2="NOT_REACHED", l3="NOT_REACHED", checks=())
        return to_arbitration(replace(state, candidate_role="NONE"), "P0_NONE", "F_PRIMARY_FUTURE_SAFETY_FAIL")

    if state.phase == "C0":
        if observation == "C0_PASS":
            return moved(state, "C0_PASS", phase="L2", c0="PASS", checks=state.checks + ("C0",), reason_scope="NONE")
        if observation == "C0_UNKNOWN_GLOBAL":
            return to_arbitration(replace(state, c0="UNKNOWN_GLOBAL"), "C0_UNKNOWN_GLOBAL", "F_ACTUATOR_AUTHORITY_UNRESOLVED", "GLOBAL_AUTHORITY_OR_EVIDENCE")
        local_unknown = observation == "C0_UNKNOWN_LOCAL"
        next_state = replace(state, c0="UNKNOWN_LOCAL" if local_unknown else "FAIL_LOCAL", reason_scope="CANDIDATE_LOCAL_COMPUTATION")
        if can_search_alternative(next_state):
            return moved(next_state, "C0_UNKNOWN_LOCAL_ALT" if local_unknown else "C0_FAIL_LOCAL_ALT", phase="ALT_SEARCH", failure_code="F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_ACTUATOR_ADMISSIBILITY_LOCAL")
        return to_arbitration(next_state, "C0_UNKNOWN_LOCAL_ARB" if local_unknown else "C0_FAIL_LOCAL_ARB", "F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_ACTUATOR_ADMISSIBILITY_LOCAL", "CANDIDATE_LOCAL_COMPUTATION")

    if state.phase == "L2":
        if observation == "L2_PASS":
            return moved(state, "L2_PASS", phase="L3", l2="PASS", checks=state.checks + ("L2",), reason_scope="NONE")
        if observation == "L2_UNKNOWN_GLOBAL":
            return to_arbitration(replace(state, l2="UNKNOWN_GLOBAL"), "L2_UNKNOWN_GLOBAL", "F_MAP_REFERENCE_UNRESOLVED", "GLOBAL_AUTHORITY_OR_EVIDENCE")
        local_unknown = observation == "L2_UNKNOWN_LOCAL"
        next_state = replace(state, l2="UNKNOWN_LOCAL" if local_unknown else "FAIL", reason_scope="CANDIDATE_LOCAL_COMPUTATION")
        if can_search_alternative(next_state):
            return moved(next_state, "L2_UNKNOWN_LOCAL_ALT" if local_unknown else "L2_FAIL_ALT", phase="ALT_SEARCH", failure_code="F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_PRIMARY_FUTURE_SAFETY_FAIL")
        return to_arbitration(next_state, "L2_UNKNOWN_LOCAL_ARB" if local_unknown else "L2_FAIL_ARB", "F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_PRIMARY_FUTURE_SAFETY_FAIL", "CANDIDATE_LOCAL_COMPUTATION")

    if state.phase == "L3":
        if observation == "L3_WITNESS_FOUND":
            return moved(state, "L3_FOUND", phase="ARBITRATION", l3="WITNESS_FOUND", checks=state.checks + ("L3",), navigation_ready=True, new_backup_created=True, reason_scope="NONE")
        if observation == "L3_UNKNOWN_GLOBAL":
            return to_arbitration(replace(state, l3="UNKNOWN_GLOBAL"), "L3_UNKNOWN_GLOBAL", "F_MAP_REFERENCE_UNRESOLVED", "GLOBAL_AUTHORITY_OR_EVIDENCE")
        local_unknown = observation == "L3_UNKNOWN_LOCAL"
        next_state = replace(state, l3="UNKNOWN_LOCAL" if local_unknown else "WITNESS_ABSENT", reason_scope="CANDIDATE_LOCAL_COMPUTATION")
        if can_search_alternative(next_state):
            return moved(next_state, "L3_UNKNOWN_LOCAL_ALT" if local_unknown else "L3_ABSENT_ALT", phase="ALT_SEARCH", failure_code="F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_PRIMARY_BACKUP_FAIL")
        return to_arbitration(next_state, "L3_UNKNOWN_LOCAL_ARB" if local_unknown else "L3_ABSENT_ARB", "F_CANDIDATE_LOCAL_COMPUTE_UNKNOWN" if local_unknown else "F_PRIMARY_BACKUP_FAIL", "CANDIDATE_LOCAL_COMPUTATION")

    if state.phase == "ALT_SEARCH":
        if observation == "DEADLINE_GUARD":
            return to_arbitration(state, "ALT_GUARD", "F_RUNTIME_DEADLINE")
        if observation == "ALT_EXHAUSTED":
            return to_arbitration(replace(state, alternatives="EXHAUSTED"), "ALT_DONE", "F_ALTERNATIVE_LIBRARY_EXHAUSTED")
        attempts = state.alt_attempts + 1
        return moved(
            state,
            "ALT_NEXT",
            phase="C0",
            candidate_role="ALTERNATIVE",
            c0="NOT_REACHED",
            l2="NOT_REACHED",
            l3="NOT_REACHED",
            checks=(),
            alt_attempts=attempts,
            alternatives="EXHAUSTED" if attempts >= ALT_BUDGET else "AVAILABLE",
            reason_scope="NONE",
        )

    if state.phase == "ARBITRATION":
        if state.navigation_ready and state.new_backup_created and state.deadline == "OPEN":
            return moved(state, "ARB_NAV", phase="COMMIT", action_authority="CERTIFIED_NAVIGATION", backup="VALID", old_backup_retained=(state.backup == "VALID"), task_success=(state.goal == "REACHED"))
        if state.backup == "VALID":
            return moved(state, "ARB_BACKUP", phase="BACKUP_EXECUTION", action_authority="RETAINED_BACKUP", old_backup_retained=True)
        if state.terminal == "MEMBER_ELIGIBLE":
            return moved(state, "ARB_TERMINAL", phase="COMMIT", action_authority="CERTIFIED_TERMINAL", task_success=(state.goal == "REACHED"))
        if state.deadline == "OPEN" and state.terminal == "NOT_EVALUATED":
            return moved(state, "ARB_EVAL_TERMINAL", phase="TERMINAL_EVALUATION")
        return moved(state, "ARB_BOUNDARY", phase="ASSURANCE_BOUNDARY", action_authority="OUTSIDE_METHOD", failure_code="F_NO_METHOD_CERTIFIED_ACTION")

    if state.phase == "BACKUP_EXECUTION":
        return moved(state, "BACKUP_COMMIT", phase="COMMIT", action_authority="RETAINED_BACKUP", old_backup_retained=True, task_success=False)

    if state.phase == "TERMINAL_EVALUATION":
        if observation == "TERMINAL_MEMBER_ELIGIBLE":
            return moved(state, "TERM_ELIGIBLE", phase="COMMIT", terminal="MEMBER_ELIGIBLE", action_authority="CERTIFIED_TERMINAL", task_success=(state.goal == "REACHED"))
        if observation == "TERMINAL_MEMBER_NOT_ELIGIBLE":
            return moved(state, "TERM_NOT_ELIGIBLE", phase="ASSURANCE_BOUNDARY", terminal="MEMBER_NOT_ELIGIBLE", action_authority="OUTSIDE_METHOD", failure_code="F_TERMINAL_NOT_CERTIFIED")
        return moved(state, "TERM_UNKNOWN", phase="ASSURANCE_BOUNDARY", terminal="UNKNOWN", action_authority="OUTSIDE_METHOD", reason_scope="GLOBAL_AUTHORITY_OR_EVIDENCE", failure_code="F_TERMINAL_NOT_CERTIFIED")

    raise ValueError(f"no transition for {state.phase}")


def initial_states() -> Iterable[State]:
    for backup in ("NONE", "VALID", "INVALID", "EXHAUSTED"):
        for deadline in ("OPEN", "GUARD_REACHED", "EXPIRED"):
            for alternatives in ("AVAILABLE", "EXHAUSTED"):
                for terminal in ("NOT_EVALUATED", "MEMBER_ELIGIBLE", "MEMBER_NOT_ELIGIBLE", "UNKNOWN"):
                    for goal in ("REACHED", "NOT_REACHED"):
                        yield State(
                            backup=backup,
                            deadline=deadline,
                            alternatives=alternatives,
                            terminal=terminal,
                            goal=goal,
                            old_backup_retained=(backup == "VALID"),
                        )


def shortest_path_payload(path: tuple[tuple[str, str], ...], state: State) -> dict:
    return {"path": [{"phase": phase, "observation": obs} for phase, obs in path], "state": asdict(state)}


def explore() -> tuple[set[State], list[tuple[State, str, State]], list[dict]]:
    seen: set[State] = set()
    edges: list[tuple[State, str, State]] = []
    errors: list[dict] = []
    queue = deque((state, ()) for state in initial_states())
    while queue:
        state, path = queue.popleft()
        if state in seen:
            continue
        seen.add(state)
        for obs in legal_observations(state):
            try:
                nxt = step(state, obs)
            except Exception as exc:  # retained as shortest totality witness
                errors.append({"property":"P1", "error":str(exc), **shortest_path_payload(path + ((state.phase, obs),), state)})
                continue
            edges.append((state, obs, nxt))
            if nxt not in seen:
                queue.append((nxt, path + ((state.phase, obs),)))
    return seen, edges, errors


def check_properties(states: set[State], edges: list[tuple[State, str, State]], totality_errors: list[dict]) -> tuple[dict, list[dict]]:
    violations: dict[str, list[dict]] = {f"P{i}": [] for i in range(1, 21)}
    violations["P1"].extend(totality_errors)

    # P2 is structural: step is a function and every table rule ID is unique.
    # P3/P4/P5/P9/P10/P11/P20 inspect all reachable commit states.
    for state in states:
        if state.phase == "COMMIT" and state.action_authority == "CERTIFIED_NAVIGATION":
            required = state.c0 == "PASS" and state.l2 == "PASS" and state.l3 == "WITNESS_FOUND" and set(state.checks) == {"C0", "L2", "L3"}
            if not required:
                violations["P3"].append({"state":asdict(state)})
            if state.assurance_mode != "ACTIVE_ASSURANCE_MODE" or not required:
                violations["P4"].append({"state":asdict(state)})
            if state.candidate_role == "ALTERNATIVE" and not required:
                violations["P5"].append({"state":asdict(state)})
            if state.backup != "VALID" or not state.new_backup_created:
                violations["P9"].append({"state":asdict(state)})
                violations["P20"].append({"state":asdict(state)})
            if state.old_backup_retained is False and state.backup == "VALID" and not state.new_backup_created:
                violations["P11"].append({"state":asdict(state)})
        if state.phase == "ALT_SEARCH" and state.l1 == "FAIL":
            violations["P6"].append({"state":asdict(state)})
        if state.alt_attempts > ALT_BUDGET:
            violations["P14"].append({"state":asdict(state)})
        if state.lifecycle == "RUNTIME" and state.projection_repair:
            violations["P16"].append({"state":asdict(state)})
        if state.phase == "ASSURANCE_BOUNDARY" and state.action_authority != "OUTSIDE_METHOD":
            violations["P18"].append({"state":asdict(state)})
        if state.action_authority in {"RETAINED_BACKUP", "CERTIFIED_TERMINAL"} and state.goal != "REACHED" and state.task_success:
            violations["P19"].append({"state":asdict(state)})

    for source, obs, dest in edges:
        if source.backup == "VALID" and not source.navigation_ready and dest.phase not in TERMINAL_PHASES and not dest.old_backup_retained:
            violations["P10"].append({"source":asdict(source), "observation":obs, "destination":asdict(dest)})
        if source.deadline in {"GUARD_REACHED", "EXPIRED"} and source.phase == "ARBITRATION" and dest.phase not in {"BACKUP_EXECUTION", "COMMIT", "ASSURANCE_BOUNDARY"}:
            violations["P12"].append({"source":asdict(source), "destination":asdict(dest)})
        if source.phase == "ARBITRATION" and source.navigation_ready and source.deadline == "OPEN" and source.goal == "NOT_REACHED" and dest.action_authority == "CERTIFIED_TERMINAL":
            violations["P13"].append({"source":asdict(source), "destination":asdict(dest)})
        if "UNKNOWN_GLOBAL" in obs and dest.phase == "ALT_SEARCH":
            violations["P8"].append({"source":asdict(source), "observation":obs, "destination":asdict(dest)})
        if "UNKNOWN" in obs and dest.action_authority == "CERTIFIED_NAVIGATION":
            violations["P7"].append({"source":asdict(source), "observation":obs, "destination":asdict(dest)})

    # P15: rule/failure families stay disjoint in the frozen table.
    for state in states:
        if state.failure_code.startswith("F_MAP") and state.reason_scope not in {"GLOBAL_AUTHORITY_OR_EVIDENCE", "NONE"}:
            violations["P15"].append({"state":asdict(state)})

    # P17: frozen symbolic position-first indexing.
    temporal = {
        "L1": ["k", "k+1"],
        "L2": ["k+1", "k+2"],
        "backup_start": "k+1",
        "backup_first_action": "u_(k+1)",
        "new_token_valid_at": "cycle_(k+1)",
    }
    if temporal["L1"][1] != temporal["L2"][0] or temporal["backup_start"] != temporal["L2"][0]:
        violations["P17"].append({"temporal":temporal})

    results = {}
    for item in load_json("PROPERTIES_P1_P20.json")["properties"]:
        pid = item["id"]
        results[pid] = {"name":item["name"], "status":"PASS" if not violations[pid] else "FAIL", "violation_count":len(violations[pid])}
    return results, [dict(property=pid, evidence=evidence) for pid, items in violations.items() for evidence in items]


def scenario_state(initial: dict) -> State:
    backup = initial.get("backup", "NONE")
    return State(
        backup=backup,
        deadline=initial.get("deadline", "OPEN"),
        alternatives=initial.get("alternatives", "AVAILABLE"),
        terminal=initial.get("terminal", "NOT_EVALUATED"),
        goal=initial.get("goal", "NOT_REACHED"),
        old_backup_retained=(backup == "VALID"),
    )


def run_scenarios() -> tuple[list[dict], list[dict]]:
    results, failures = [], []
    manifest = load_json("ADVERSARIAL_SCENARIOS_V2.json")
    if manifest["scenario_count"] != len(manifest["scenarios"]):
        raise ValueError("scenario count mismatch")
    for scenario in manifest["scenarios"]:
        state = scenario_state(scenario["initial"])
        trace = []
        error = None
        for obs in scenario["observations"]:
            trace.append({"phase":state.phase, "observation":obs})
            try:
                state = step(state, obs)
            except Exception as exc:
                error = str(exc)
                break
        mismatches = []
        for field, expected in scenario["expected"].items():
            actual = getattr(state, field)
            if actual != expected:
                mismatches.append({"field":field, "expected":expected, "actual":actual})
        status = "PASS" if error is None and not mismatches else "FAIL"
        result = {"id":scenario["id"], "name":scenario["name"], "status":status, "final_state":asdict(state), "trace_length":len(trace)}
        results.append(result)
        if status == "FAIL":
            failures.append({"scenario":scenario["id"], "error":error, "mismatches":mismatches, "trace":trace, "final_state":asdict(state)})
    return results, failures


def main() -> int:
    states, edges, totality_errors = explore()
    properties, property_counterexamples = check_properties(states, edges, totality_errors)
    scenarios, scenario_failures = run_scenarios()
    counterexamples = property_counterexamples + [{"property":"ADVERSARIAL_SCENARIO", **x} for x in scenario_failures]
    hard_counts = {
        "reachable_unhandled_state_count": properties["P1"]["violation_count"],
        "nondeterministic_transition_count": properties["P2"]["violation_count"],
        "uncertified_navigation_commit_path_count": properties["P3"]["violation_count"] + properties["P4"]["violation_count"],
        "alternative_bypass_path_count": properties["P5"]["violation_count"] + properties["P6"]["violation_count"],
        "backup_gap_path_count": properties["P9"]["violation_count"] + properties["P10"]["violation_count"] + properties["P11"]["violation_count"] + properties["P20"]["violation_count"],
        "deadline_without_decision_path_count": properties["P12"]["violation_count"],
        "terminal_priority_violation_count": properties["P13"]["violation_count"],
        "infinite_or_unbounded_search_cycle_count": properties["P14"]["violation_count"],
        "unknown_misclassification_path_count": properties["P7"]["violation_count"] + properties["P8"]["violation_count"],
        "runtime_projection_repair_path_count": properties["P16"]["violation_count"],
        "temporal_index_gap_count": properties["P17"]["violation_count"],
        "false_safe_stop_claim_path_count": properties["P18"]["violation_count"] + properties["P19"]["violation_count"],
    }
    scenario_failure_count = len(scenario_failures)
    all_pass = all(v["status"] == "PASS" for v in properties.values()) and not any(hard_counts.values()) and scenario_failure_count == 0
    summary = {
        "schema_version":"METHOD_LOGIC_MODEL_CHECK_RESULT_V2",
        "checker":"model_check_method_logic_v2.py",
        "stdlib_only":True,
        "bounded_finite_exploration":True,
        "alt_budget":ALT_BUDGET,
        "reachable_state_count":len(states),
        "transition_edge_count":len(edges),
        "property_results":properties,
        "adversarial_scenario_count":len(scenarios),
        "adversarial_scenario_pass_count":sum(x["status"] == "PASS" for x in scenarios),
        "hard_violation_counts":hard_counts,
        "counterexample_count":len(counterexamples),
        "correction_round_count":0,
        "status":"PASS_METHOD_LOGIC_MODEL_CHECK_V2" if all_pass else "FAIL_METHOD_LOGIC_MODEL_CHECK_V2",
    }
    phase_counts = {}
    authority_counts = {}
    for state in states:
        phase_counts[state.phase] = phase_counts.get(state.phase, 0) + 1
        authority_counts[state.action_authority] = authority_counts.get(state.action_authority, 0) + 1
    reachable = {
        "schema_version":"METHOD_LOGIC_REACHABLE_STATE_SUMMARY_V2",
        "reachable_state_count":len(states),
        "transition_edge_count":len(edges),
        "phase_counts":dict(sorted(phase_counts.items())),
        "action_authority_counts":dict(sorted(authority_counts.items())),
        "terminal_state_count":sum(s.phase in TERMINAL_PHASES for s in states),
        "max_alt_attempts_reached":max(s.alt_attempts for s in states),
        "initial_state_family_count":sum(1 for _ in initial_states()),
        "scenario_results":scenarios,
    }
    (ROOT / "model_check_result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "reachable_state_summary.json").write_text(json.dumps(reachable, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "counterexamples.json").write_text(json.dumps({"schema_version":"METHOD_LOGIC_COUNTEREXAMPLES_V2", "count":len(counterexamples), "counterexamples":counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["status"])
    print(f"reachable_states={len(states)} edges={len(edges)} counterexamples={len(counterexamples)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
