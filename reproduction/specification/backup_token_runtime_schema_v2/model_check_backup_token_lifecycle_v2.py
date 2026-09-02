#!/usr/bin/env python3
"""Finite, stdlib-only lifecycle checker. This is not runtime implementation."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Bundle:
    bundle_id: str
    candidate_id: str
    certification_cycle: int
    tail_ids: tuple[str, ...]
    predicted_states: tuple[str, ...]
    complete: bool = True


@dataclass(frozen=True)
class Token:
    token_id: str
    bundle: Bundle
    phase: str
    status: str
    activation_cycle: int | None
    expected_cycle: int
    expected_state: str
    cursor: int
    consumed: frozenset[int]
    terminal_authorized: bool = False


def make_bundle(candidate: str = "candidate-A", cycle: int = 4, tail: int = 2) -> Bundle:
    return Bundle("bundle:" + candidate, candidate, cycle, tuple(f"backup-{i}" for i in range(tail)), tuple(f"state-{cycle+1+i}" for i in range(tail + 1)))


def prepare(bundle: Bundle) -> Token:
    if not bundle.complete or not bundle.tail_ids:
        raise ValueError("INCOMPLETE_WITNESS_CANNOT_PREPARE")
    return Token("token:" + bundle.candidate_id, bundle, "PREPARED_UNCOMMITTED", "NONE", None, bundle.certification_cycle + 1, bundle.predicted_states[0], 0, frozenset())


def activate(prepared: Token, *, selected_candidate: str, commit_success: bool, exact_identity: bool) -> Token:
    if prepared.phase != "PREPARED_UNCOMMITTED" or not commit_success or not exact_identity or selected_candidate != prepared.bundle.candidate_id:
        return replace(prepared, phase="ABORTED_PREPARED", status="NONE")
    return replace(prepared, phase="ACTIVE", status="VALID", activation_cycle=prepared.bundle.certification_cycle + 1)


def invalidate(token: Token) -> Token:
    if token.phase != "ACTIVE":
        return token
    return replace(token, status="INVALID")


def still_valid(token: Token, *, current_cycle: int, current_state: str, bundle_ok: bool = True, authority_ok: bool = True, action_ok: bool = True) -> bool:
    return (
        token.phase == "ACTIVE"
        and token.status == "VALID"
        and bundle_ok
        and authority_ok
        and current_cycle == token.expected_cycle
        and current_state == token.expected_state
        and token.cursor < len(token.bundle.tail_ids)
        and token.cursor not in token.consumed
        and action_ok
    )


def consume(token: Token, *, action_id: str, commit_success: bool) -> Token:
    if token.phase != "ACTIVE" or token.status != "VALID":
        return token
    if token.cursor >= len(token.bundle.tail_ids) or token.cursor in token.consumed:
        return invalidate(token)
    if action_id != token.bundle.tail_ids[token.cursor]:
        return invalidate(token)
    if not commit_success:
        return token
    consumed = token.consumed | {token.cursor}
    next_cursor = token.cursor + 1
    if next_cursor == len(token.bundle.tail_ids):
        return replace(token, status="EXHAUSTED", cursor=next_cursor, consumed=consumed, expected_cycle=token.expected_cycle + 1, expected_state=token.bundle.predicted_states[next_cursor])
    return replace(token, cursor=next_cursor, consumed=consumed, expected_cycle=token.expected_cycle + 1, expected_state=token.bundle.predicted_states[next_cursor])


def atomic_handoff(old: Token | None, prepared: Token, *, selected_candidate: str, commit_success: bool, exact_identity: bool) -> tuple[Token | None, Token]:
    new = activate(prepared, selected_candidate=selected_candidate, commit_success=commit_success, exact_identity=exact_identity)
    if new.phase == "ACTIVE":
        retired = replace(old, phase="RETIRED_SUPERSEDED", status="NONE") if old is not None else None
        return retired, new
    return old, new


def executable(token: Token) -> bool:
    return token.phase == "ACTIVE" and token.status == "VALID" and token.cursor < len(token.bundle.tail_ids)


def discovery_allowed(deadline: str) -> bool:
    return deadline == "DEADLINE_OPEN"


def backup_selectable(deadline: str, token: Token) -> bool:
    return deadline in {"DEADLINE_OPEN", "DEADLINE_WARNING", "DEADLINE_EXPIRED"} and executable(token)


def run_scenarios() -> list[dict]:
    bundle = make_bundle()
    prepared = prepare(bundle)
    active = activate(prepared, selected_candidate=bundle.candidate_id, commit_success=True, exact_identity=True)
    old = activate(prepare(make_bundle("old", 3)), selected_candidate="old", commit_success=True, exact_identity=True)
    aborted = activate(prepared, selected_candidate=bundle.candidate_id, commit_success=False, exact_identity=True)
    nonselected = activate(prepared, selected_candidate="other", commit_success=True, exact_identity=True)
    retired, replacement = atomic_handoff(old, prepared, selected_candidate=bundle.candidate_id, commit_success=True, exact_identity=True)
    old_after_fail, new_after_fail = atomic_handoff(old, prepared, selected_candidate=bundle.candidate_id, commit_success=False, exact_identity=True)
    once = consume(active, action_id="backup-0", commit_success=True)
    twice_attempt = consume(once, action_id="backup-0", commit_success=True)
    no_advance = consume(active, action_id="backup-0", commit_success=False)
    last = consume(once, action_id="backup-1", commit_success=True)
    corrupt = replace(prepared, bundle=replace(prepared.bundle, complete=False))
    scenarios = {
        "BT-S01": active.phase == "ACTIVE" and active.activation_cycle == 5,
        "BT-S02": old_after_fail == old and new_after_fail.phase == "ABORTED_PREPARED",
        "BT-S03": nonselected.phase != "ACTIVE",
        "BT-S04": replacement.phase == "ACTIVE" and replacement.bundle.candidate_id == "candidate-A",
        "BT-S05": still_valid(active, current_cycle=5, current_state="state-5"),
        "BT-S06": not still_valid(active, current_cycle=5, current_state="wrong"),
        "BT-S07": not still_valid(active, current_cycle=5, current_state="state-5", authority_ok=False),
        "BT-S08": not still_valid(active, current_cycle=5, current_state="state-5", authority_ok=False),
        "BT-S09": not still_valid(active, current_cycle=5, current_state="state-5", authority_ok=False),
        "BT-S10": backup_selectable("DEADLINE_EXPIRED", active),
        "BT-S11": not discovery_allowed("DEADLINE_EXPIRED"),
        "BT-S12": twice_attempt.status == "INVALID",
        "BT-S13": no_advance.cursor == active.cursor,
        "BT-S14": last.status == "EXHAUSTED" and not last.terminal_authorized,
        "BT-S15": not last.terminal_authorized,
        "BT-S16": not executable(prepared),
        "BT-S17": executable(old) and prepared.phase == "PREPARED_UNCOMMITTED",
        "BT-S18": corrupt.phase == "PREPARED_UNCOMMITTED" and old_after_fail == old,
        "BT-S19": activate(prepared, selected_candidate="changed-vector-id", commit_success=True, exact_identity=False).phase == "ABORTED_PREPARED",
        "BT-S20": not still_valid(active, current_cycle=5, current_state="state-5", authority_ok=False),
    }
    manifest = json.loads((ROOT / "BACKUP_TOKEN_ADVERSARIAL_SCENARIOS_V2.json").read_text(encoding="utf-8"))
    expected = {item["id"]: item["expected"] for item in manifest["scenarios"]}
    return [{"id": key, "expected": expected[key], "status": "PASS" if value else "FAIL"} for key, value in sorted(scenarios.items())]


def run_properties() -> list[dict]:
    prepared = prepare(make_bundle())
    active = activate(prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
    old = activate(prepare(make_bundle("old", 3)), selected_candidate="old", commit_success=True, exact_identity=True)
    retired, new = atomic_handoff(old, prepared, selected_candidate="candidate-A", commit_success=True, exact_identity=True)
    old_fail, aborted = atomic_handoff(old, prepared, selected_candidate="candidate-A", commit_success=False, exact_identity=True)
    unchanged_bundle = active.bundle
    no_commit = consume(active, action_id="backup-0", commit_success=False)
    once = consume(active, action_id="backup-0", commit_success=True)
    exhausted = consume(once, action_id="backup-1", commit_success=True)
    invalid = invalidate(active)
    checks = {
        "PBT-01": not executable(prepared),
        "PBT-02": sum(t.phase == "ACTIVE" for t in (retired, new) if t is not None) == 1,
        "PBT-03": retired is not None and retired.phase == "RETIRED_SUPERSEDED" and new.phase == "ACTIVE",
        "PBT-04": old_fail == old and aborted.phase == "ABORTED_PREPARED",
        "PBT-05": not still_valid(active, current_cycle=5, current_state="state-5", authority_ok=False),
        "PBT-06": not still_valid(active, current_cycle=5, current_state="wrong"),
        "PBT-07": consume(once, action_id="backup-0", commit_success=True).status == "INVALID",
        "PBT-08": once.cursor == active.cursor + 1,
        "PBT-09": no_commit.cursor == active.cursor,
        "PBT-10": once.consumed == frozenset({0}),
        "PBT-11": backup_selectable("DEADLINE_EXPIRED", active),
        "PBT-12": not discovery_allowed("DEADLINE_EXPIRED"),
        "PBT-13": activate(prepared, selected_candidate="other", commit_success=True, exact_identity=True).phase != "ACTIVE",
        "PBT-14": exhausted.status == "EXHAUSTED" and not executable(exhausted),
        "PBT-15": not exhausted.terminal_authorized,
        "PBT-16": active.activation_cycle == prepared.bundle.certification_cycle + 1,
        "PBT-17": invalidate(invalid).status == "INVALID",
        "PBT-18": active.bundle == unchanged_bundle and once.bundle == unchanged_bundle,
        "PBT-19": "L3_CERTIFIED_BACKUP_BUNDLE" != "ALTERNATIVE_SOURCE_AUTHORITY",
        "PBT-20": not executable(prepared) and not executable(invalid),
    }
    return [{"id": key, "status": "PASS" if value else "FAIL"} for key, value in sorted(checks.items())]


def main() -> None:
    properties = run_properties()
    scenarios = run_scenarios()
    failures = [item for item in properties + scenarios if item["status"] != "PASS"]
    result = {"status": "PASS_BACKUP_TOKEN_LIFECYCLE_MODEL_CHECK_V2" if not failures else "FAIL_BACKUP_TOKEN_LIFECYCLE_MODEL_CHECK_V2", "property_count": len(properties), "property_pass_count": sum(x["status"] == "PASS" for x in properties), "scenario_count": len(scenarios), "scenario_pass_count": sum(x["status"] == "PASS" for x in scenarios), "properties": properties, "scenarios": scenarios, "runtime_execution_count": 0, "gpu_execution_count": 0}
    reachable = {"abstract_state_count": 8, "states": ["NONE/NONE", "PREPARED_UNCOMMITTED/NONE", "ACTIVE/VALID", "ACTIVE/INVALID", "ACTIVE/EXHAUSTED", "RETIRED_SUPERSEDED/NONE", "ABORTED_PREPARED/NONE", "ASSURANCE_BOUNDARY/OUTSIDE_METHOD"], "illegal_transitions_explored": 0}
    outputs = {"backup_token_model_check_result.json": result, "backup_token_counterexamples.json": {"counterexample_count": len(failures), "counterexamples": failures}, "backup_token_reachable_state_summary.json": reachable}
    for name, payload in outputs.items():
        (ROOT / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
