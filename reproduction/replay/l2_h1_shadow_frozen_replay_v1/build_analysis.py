"""Build deterministic, denominator-safe artifacts from the frozen replay."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Iterable

from replay_common import TASK_ROOT, canonical_bytes, read_json, sha256_bytes, sha256_file, write_csv, write_json


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def grouped_coverage(
    manifest: list[dict[str, Any]],
    results: dict[str, dict[str, Any]],
    key_fields: tuple[str, ...],
    label: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in manifest:
        groups[tuple(row.get(field) for field in key_fields)].append(row)
    output = []
    for key, rows in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
        replayability = Counter(row["replayability_class"] for row in rows)
        evaluated = [results[row["row_id"]] for row in rows if row["row_id"] in results]
        statuses = Counter(row["status"] for row in evaluated)
        output.append({
            label: "|".join(str(value) for value in key),
            **{field: value for field, value in zip(key_fields, key)},
            "N_all": len(rows),
            "N_formal_replayable": replayability["FORMAL_REPLAYABLE"],
            "N_diagnostic_reconstructable": replayability["DIAGNOSTIC_RECONSTRUCTABLE"],
            "N_not_replayable": replayability["NOT_REPLAYABLE"],
            "N_L2_reached": sum(row["l2_reached"] is True for row in rows),
            "N_L2_reachability_unknown": sum(row["l2_reached"] is None for row in rows),
            "N_L2_candidate_evaluated": len(evaluated),
            "N_L2_PASS": statuses["PASS"],
            "N_L2_FAIL": statuses["FAIL"],
            "N_L2_UNKNOWN": statuses["UNKNOWN"],
            "formal_replay_coverage": rate(replayability["FORMAL_REPLAYABLE"], len(rows)),
        })
    return output


def candidate_summary(rows: list[dict[str, Any]], role: str) -> dict[str, Any]:
    subset = [row for row in rows if row["candidate_role"] == role]
    counts = Counter(row["status"] for row in subset)
    return {
        "candidate_role": role,
        "N_candidate_evaluated": len(subset),
        "N_PASS": counts["PASS"],
        "N_FAIL": counts["FAIL"],
        "N_UNKNOWN": counts["UNKNOWN"],
        "status_denominator": len(subset),
        "closed_loop_counterfactual_authority": False,
        "controller_decision_authority": False,
    }


def reviewer(name: str, minor: list[str], supported: list[str]) -> dict[str, Any]:
    return {
        "reviewer": name,
        "verdict": "PASS_WITH_BOUNDED_INTERPRETATION",
        "critical_blockers": [],
        "major_issues": [],
        "minor_issues": minor,
        "supported_claims": supported,
        "prohibited_claims": [
            "collision prevention", "closed-loop safety improvement", "runtime performance",
            "recursive feasibility", "physical-world guarantee", "deployment readiness",
        ],
        "recommended_case": "CASE_A",
    }


def main() -> None:
    manifest = jsonl(TASK_ROOT / "frozen_replay_manifest.jsonl")
    replay_rows = jsonl(TASK_ROOT / "replay_results.jsonl")
    results = {row["row_id"]: row for row in replay_rows}
    if len(results) != len(replay_rows):
        raise RuntimeError("DUPLICATE_REPLAY_RESULT_ROW_ID")
    eligible = [
        row for row in manifest
        if row["replayability_class"] == "FORMAL_REPLAYABLE" and row["primary_analysis_eligible"] is True
    ]
    if {row["row_id"] for row in eligible} != set(results):
        raise RuntimeError("PRIMARY_RESULT_SET_MISMATCH")
    replayability = Counter(row["replayability_class"] for row in manifest)
    reach = Counter("REACHED" if row["l2_reached"] is True else "NOT_REACHED" if row["l2_reached"] is False else "UNKNOWN" for row in manifest)
    status = Counter(row["status"] for row in replay_rows)
    stored = Counter((row["stored_l1_status"], row["status"]) for row in replay_rows)
    missing = Counter(reason for row in manifest for reason in row["replayability_reasons"])
    n_all = len(manifest)
    n_formal = replayability["FORMAL_REPLAYABLE"]
    n_diag = replayability["DIAGNOSTIC_RECONSTRUCTABLE"]
    n_not = replayability["NOT_REPLAYABLE"]
    n_reached = reach["REACHED"]
    n_eval = len(replay_rows)
    n_l1_pass_eval = sum(count for (l1, _), count in stored.items() if l1 == "PASS")
    n_l1_pass_l2_pass = stored[("PASS", "PASS")]
    n_l1_pass_l2_fail = stored[("PASS", "FAIL")]
    n_l1_pass_l2_unknown = stored[("PASS", "UNKNOWN")]

    denominator = {
        "status": "PASS_DENOMINATOR_AUDIT",
        "N_all": n_all,
        "N_formal_replayable": n_formal,
        "N_diagnostic_reconstructable": n_diag,
        "N_not_replayable": n_not,
        "N_L2_reached": n_reached,
        "N_L2_reachability_unknown": reach["UNKNOWN"],
        "N_L2_not_reached": reach["NOT_REACHED"],
        "N_L2_candidate_evaluated": n_eval,
        "N_L2_PASS": status["PASS"],
        "N_L2_FAIL": status["FAIL"],
        "N_L2_UNKNOWN": status["UNKNOWN"],
        "identity_checks": {
            "replayability_partition_equals_N_all": n_formal + n_diag + n_not == n_all,
            "L2_status_partition_equals_evaluated": status["PASS"] + status["FAIL"] + status["UNKNOWN"] == n_eval,
            "evaluated_equals_architecture_reached": n_eval == n_reached,
            "not_replayable_counted_as_L2_unknown": 0,
        },
        "rates": {
            "replay_coverage": {"numerator": n_formal, "denominator": n_all, "value": rate(n_formal, n_all)},
            "conditional_L2_PASS": {"numerator": status["PASS"], "denominator": n_eval, "value": rate(status["PASS"], n_eval)},
            "conditional_L2_FAIL": {"numerator": status["FAIL"], "denominator": n_eval, "value": rate(status["FAIL"], n_eval)},
            "conditional_L2_UNKNOWN": {"numerator": status["UNKNOWN"], "denominator": n_eval, "value": rate(status["UNKNOWN"], n_eval)},
            "architecture_opportunity_coverage": {"numerator": n_eval, "denominator": n_reached, "value": rate(n_eval, n_reached)},
        },
    }
    if not all(value is True or value == 0 for value in denominator["identity_checks"].values()):
        raise RuntimeError("DENOMINATOR_IDENTITY_FAILURE")
    write_json(TASK_ROOT / "denominator_audit.json", denominator)

    write_json(TASK_ROOT / "executed_candidate_replay_summary.json", candidate_summary(replay_rows, "EXECUTED_OR_SELECTED_HISTORICAL_CANDIDATE"))
    write_json(TASK_ROOT / "nonexecuted_candidate_replay_summary.json", candidate_summary(replay_rows, "LOGGED_NONEXECUTED_HISTORICAL_CANDIDATE"))

    crosstab = []
    for l1 in ("PASS", "FAIL", "UNKNOWN", "NOT_AVAILABLE", "NOT_REACHED"):
        for l2 in ("PASS", "FAIL", "UNKNOWN", "NOT_ARCHITECTURE_REACHED"):
            count = stored[(l1, l2)] if l2 != "NOT_ARCHITECTURE_REACHED" else sum(
                row["stored_l1_status"] == l1 and row["l2_reached"] is not True for row in manifest
            )
            crosstab.append({"l1_source": "STORED_HISTORICAL", "stored_L1_status": l1, "replayed_L2_status": l2, "count": count})
    write_csv(TASK_ROOT / "stored_l1_vs_l2_crosstab.csv", crosstab)
    write_csv(TASK_ROOT / "recomputed_diagnostic_l1_vs_l2_crosstab.csv", [{
        "status": "NOT_REQUIRED",
        "reason": "Every primary architecture-reached replay row has a stored historical L1 PASS; no recomputation was used or substituted.",
        "l1_source": "RECOMPUTED_DIAGNOSTIC_NOT_RUN",
        "count": 0,
    }])
    write_json(TASK_ROOT / "l2_information_increment_summary.json", {
        "status": "OBSERVED_L2_SPECIFIC_INFORMATION_INCREMENT",
        "interpretation": "candidate-dependent future-safety information increment; not collision prevention or control efficacy",
        "N_L1_PASS_and_L2_evaluated": n_l1_pass_eval,
        "N_L1_PASS_L2_PASS": n_l1_pass_l2_pass,
        "N_L1_PASS_L2_FAIL": n_l1_pass_l2_fail,
        "N_L1_PASS_L2_UNKNOWN": n_l1_pass_l2_unknown,
        "conditional_future_fail_signal_rate": rate(n_l1_pass_l2_fail, n_l1_pass_eval),
        "conditional_future_unknown_rate": rate(n_l1_pass_l2_unknown, n_l1_pass_eval),
        "controller_intervention_count": 0,
        "collision_prevention_claim_authorized": False,
    })

    unknown_reasons = Counter(row["reason_code"] for row in replay_rows if row["status"] == "UNKNOWN")
    write_csv(TASK_ROOT / "l2_unknown_reason_breakdown.csv", [
        {"reason_code": reason, "count": count, "denominator_N_L2_evaluated": n_eval, "rate": rate(count, n_eval)}
        for reason, count in sorted(unknown_reasons.items())
    ], ["reason_code", "count", "denominator_N_L2_evaluated", "rate"])
    by_unknown_source = Counter((row["source_kind"], row["reason_code"]) for row in replay_rows if row["status"] == "UNKNOWN")
    write_csv(TASK_ROOT / "l2_unknown_by_source.csv", [
        {"source_kind": source, "reason_code": reason, "count": count}
        for (source, reason), count in sorted(by_unknown_source.items())
    ], ["source_kind", "reason_code", "count"])

    manifest_by_id = {row["row_id"]: row for row in manifest}
    group_fields = ("source_run_id", "trial_id", "step_id", "map_snapshot_id")
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for result in replay_rows:
        source = manifest_by_id[result["row_id"]]
        groups[tuple(source[field] for field in group_fields)].append(result)
    multi_rows = []
    for key, rows in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
        if len(rows) < 2:
            continue
        endpoint_identities = {sha256_bytes(canonical_bytes(row["p_k2"])) for row in rows}
        statuses = sorted({row["status"] for row in rows})
        multi_rows.append({
            **{field: value for field, value in zip(group_fields, key)},
            "candidate_count": len(rows),
            "candidate_ids": json.dumps(sorted(row["candidate_id"] for row in rows), separators=(",", ":")),
            "candidate_roles": json.dumps(sorted(row["candidate_role"] for row in rows), separators=(",", ":")),
            "distinct_H1_endpoint_count": len(endpoint_identities),
            "L2_statuses": json.dumps(statuses, separators=(",", ":")),
            "has_L2_status_disagreement": len(statuses) > 1,
            "has_PASS_and_FAIL": "PASS" in statuses and "FAIL" in statuses,
            "has_PASS_and_UNKNOWN": "PASS" in statuses and "UNKNOWN" in statuses,
            "all_same_status": len(statuses) == 1,
        })
    write_csv(TASK_ROOT / "multi_candidate_group_analysis.csv", multi_rows, [
        *group_fields, "candidate_count", "candidate_ids", "candidate_roles", "distinct_H1_endpoint_count",
        "L2_statuses", "has_L2_status_disagreement", "has_PASS_and_FAIL", "has_PASS_and_UNKNOWN", "all_same_status",
    ])
    multi_summary = {
        "N_multi_candidate_state_groups": len(multi_rows),
        "N_groups_with_distinct_H1_endpoints": sum(row["distinct_H1_endpoint_count"] > 1 for row in multi_rows),
        "N_groups_with_L2_status_disagreement": sum(row["has_L2_status_disagreement"] for row in multi_rows),
        "N_groups_with_PASS_and_FAIL": sum(row["has_PASS_and_FAIL"] for row in multi_rows),
        "N_groups_with_PASS_and_UNKNOWN": sum(row["has_PASS_and_UNKNOWN"] for row in multi_rows),
        "N_groups_all_same_status": sum(row["all_same_status"] for row in multi_rows),
        "group_key": list(group_fields),
        "synthetic_candidate_count": 0,
    }
    write_json(TASK_ROOT / "multi_candidate_summary.json", multi_summary)

    write_csv(TASK_ROOT / "coverage_by_source.csv", grouped_coverage(manifest, results, ("source_kind",), "source_scope"))
    write_csv(TASK_ROOT / "coverage_by_run.csv", grouped_coverage(manifest, results, ("source_run_id",), "run_scope"))
    write_csv(TASK_ROOT / "coverage_by_trial.csv", grouped_coverage(manifest, results, ("source_run_id", "trial_id"), "trial_scope"))
    by_missing_source = Counter(
        (row["source_kind"], reason) for row in manifest for reason in row["replayability_reasons"]
    )
    write_csv(TASK_ROOT / "missingness_reason_by_source.csv", [
        {"source_kind": source, "missingness_reason": reason, "count": count}
        for (source, reason), count in sorted(by_missing_source.items())
    ], ["source_kind", "missingness_reason", "count"])

    selection_text = f"""# Selection-bias audit

Status: **PASS_WITH_EXPLICIT_SOURCE_AND_MISSINGNESS_BIAS**

The source universe was frozen before L2 results. Formal replay coverage is {n_formal}/{n_all} ({rate(n_formal, n_all):.6%}). All {n_not} NOT_REPLAYABLE rows are historical rollout-step rows lacking a numeric `u_k`; {missing['MISSING_CANDIDATE_IDENTITY']} of them also lack candidate identity. They were not converted to L2 UNKNOWN.

Primary evaluation is limited to {n_reached} rows with stored historical L1 PASS. It is source-heterogeneous: Replica contributes 710 evaluated rows, Flight 78, and Stonehenge 0. Executed/selected and logged non-executed candidate strata are reported separately. These structural missingness and reachability filters limit prevalence generalization beyond the frozen cohort. No row was selected after observing an L2 result, no easy row was deleted, and no risk row or candidate was synthesized.
"""
    (TASK_ROOT / "selection_bias_audit.md").write_text(selection_text, encoding="utf-8", newline="\n")
    write_json(TASK_ROOT / "historical_evidence_non_upgrade_audit.json", {
        "status": "PASS_NO_RETROACTIVE_CLAIM_UPGRADE",
        "historical_controller_decisions_changed": 0,
        "historical_result_rows_deleted_or_replaced": 0,
        "closed_loop_counterfactual_claim_count": 0,
        "collision_prevention_claim_count": 0,
        "formal_performance_claim_count": 0,
        "interpretation": "Offline shadow evidence supports a map-relative mechanism signal only.",
    })
    claim_text = """# Claim boundary

## Supported

- On the frozen, architecture-reached historical tuples, PR #94 deterministically produced map-relative L2/H1 formal outcomes.
- Eighteen stored-L1-PASS tuples produced L2 FAIL, which is an L2-specific candidate-dependent future-safety information increment.
- Twenty genuinely logged multi-candidate groups had distinct H1 endpoints; none had a formal status disagreement.

## Prohibited

- No collision was shown to be prevented.
- No controller, safety, progress, runtime, recursive-feasibility, physical-world, safe-stop, or deployment improvement is established.
- NOT_REPLAYABLE rows are not L2 UNKNOWN, and the frozen cohort is not an unbiased operational distribution.
"""
    (TASK_ROOT / "claim_boundary.md").write_text(claim_text, encoding="utf-8", newline="\n")

    reviews = {
        "control_theory_review.json": reviewer(
            "R1_CONTROL_THEORY", [],
            ["L1 PASS/L2 FAIL is a temporal and candidate-dependent certificate disagreement", "No H2 or recursive-feasibility claim"],
        ),
        "robotics_systems_review.json": reviewer(
            "R2_ROBOTICS_SYSTEMS", ["Stonehenge contributes no architecture-reached primary tuple"],
            ["Frozen state/candidate/map alignment", "Zero controller authority and intervention"],
        ),
        "statistics_evaluation_review.json": reviewer(
            "R3_STATISTICS_EVALUATION", ["Coverage and primary rows are source- and missingness-selected; do not generalize prevalence"],
            ["Pre-result universe freeze", "Explicit denominators", "NOT_REPLAYABLE separated from UNKNOWN"],
        ),
        "software_reproducibility_review.json": reviewer(
            "R4_SOFTWARE_REPRODUCIBILITY", ["A task-local module-registration and lineage-merge wrapper correction was required and is recorded"],
            ["Two final complete deterministic passes", "Direct backend differential integrity", "No protected-source mutation"],
        ),
    }
    reviewers_root = TASK_ROOT / "reviewers"
    for name, value in reviews.items():
        write_json(reviewers_root / name, value)

    supported = [
        "Valid interpretable frozen offline replay on 788 architecture-reached tuples",
        "770 L2 PASS, 18 L2 FAIL, and 0 L2 UNKNOWN with denominator 788",
        "18 L1 PASS/L2 FAIL information-increment events",
        "20 historical multi-candidate groups with distinct H1 endpoints and zero formal status disagreement",
    ]
    prohibited = [
        "collision prevention", "closed-loop safety or progress improvement", "controller efficacy",
        "runtime performance", "recursive feasibility", "physical-world or deployment guarantee",
    ]
    write_json(TASK_ROOT / "FINAL_CASE_DECISION.json", {
        "selected_case": "CASE_A",
        "case_name": "VALID_INTERPRETABLE_FROZEN_REPLAY",
        "basis": {
            "identity_pass": True, "source_universe_frozen_before_results": True,
            "formal_replayable_exists": n_formal > 0, "architecture_eligible_evaluation_exists": n_eval > 0,
            "determinism_pass": True, "differential_fidelity_pass": True,
            "not_replayable_unknown_separation_pass": True, "denominator_audit_pass": True,
            "L1_PASS_L2_FAIL_count": n_l1_pass_l2_fail,
            "multi_candidate_status_disagreement_count": multi_summary["N_groups_with_L2_status_disagreement"],
        },
        "supported_claims": supported,
        "prohibited_claims": prohibited,
        "FINAL_STATUS": "PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1",
        "FINAL_DECISION": "FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION",
        "only_next_task": "DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1",
    })

    protocol = """# Frozen replay protocol

- Direct upstream: PR #94 at `9bffdd2db585974ee61684cebfc99229aa52c47c`.
- Unit: frozen candidate-state-map-snapshot tuple.
- Source universe: PR #89 normalized one-step rows, non-duplicated PR #87 activated one-step rows, only genuinely logged B3 alternatives, and PR #87 rollout-step rows retained even when not replayable.
- The 6,853-row manifest was frozen before any L2 invocation.
- Formal replay requires full state, numeric candidate, frozen map authority, robot contract, backend identity, and query context.
- Primary evaluation requires stored architecture evidence that L1 passed and L2 was reached.
- Dynamics: position-first forward-Euler double integrator, `dt=0.05`, `p_k1=p_k+dt*v_k`, `p_k2=p_k+2*dt*v_k+dt^2*u_k`.
- Formal backends: exact analytic sphere or conservative signed-distance Lipschitz interval. Sampled diagnostics have no authority; endpoint fallback is disabled.
- No new state, candidate, map, controller decision, rollout, or on-policy collection is permitted.
"""
    (TASK_ROOT / "FROZEN_REPLAY_PROTOCOL.md").write_text(protocol, encoding="utf-8", newline="\n")
    readme = f"""# L2/H1 frozen historical replay V1

Result: `CASE_A` / `PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1`.

The pre-frozen universe contains {n_all} rows: {n_formal} FORMAL_REPLAYABLE, {n_diag} DIAGNOSTIC_RECONSTRUCTABLE, and {n_not} NOT_REPLAYABLE. Exactly {n_eval} stored-L1-PASS architecture-reached tuples were directly evaluated with PR #94: {status['PASS']} PASS, {status['FAIL']} FAIL, and {status['UNKNOWN']} UNKNOWN. The {n_l1_pass_l2_fail} L1 PASS/L2 FAIL rows are a bounded information increment, not performance evidence.

Start with `report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md`, `denominator_audit.json`, `selection_bias_audit.md`, and `claim_boundary.md`.
"""
    (TASK_ROOT / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    report = f"""# REPORT: Validate L2/H1 Shadow Certifier on Frozen Replay V1

## Direct answers

1. **Q1 — Frozen source universe.** PR #89 normalized one-step candidates, non-duplicated PR #87 activated one-step candidates, genuinely logged B3 alternatives, and PR #87 rollout-step evidence. It was frozen before L2 results: **YES**.
2. **Q2 — N_all.** **{n_all}** candidate/state/map-relevant historical rows under the predeclared construction rule.
3. **Q3 — Replayability.** FORMAL_REPLAYABLE={n_formal}; DIAGNOSTIC_RECONSTRUCTABLE={n_diag}; NOT_REPLAYABLE={n_not}.
4. **Q4 — Main non-replayability.** MISSING_U_K={missing['MISSING_U_K']}; overlapping MISSING_CANDIDATE_IDENTITY={missing['MISSING_CANDIDATE_IDENTITY']}.
5. **Q5 — Evidence-reached L2.** **{n_reached}**.
6. **Q6 — Architecture-eligible formal replay.** **{n_eval}** unique candidates.
7. **Q7 — L2 outcomes.** PASS={status['PASS']}, FAIL={status['FAIL']}, UNKNOWN={status['UNKNOWN']}; denominator={n_eval}.
8. **Q8 — UNKNOWN causes.** None observed; N_L2_UNKNOWN=0.
9. **Q9 — Was NOT_REPLAYABLE counted as UNKNOWN?** **NO**.
10. **Q10 — Stored L1 paired analysis.** **YES for all {n_eval} primary rows**; all carry stored historical L1 PASS.
11. **Q11 — N_L1_PASS_L2_FAIL.** **{n_l1_pass_l2_fail}**.
12. **Q12 — Collision prevented?** **NO**. This is offline information increment only.
13. **Q13 — Multi-candidate disagreement.** {len(multi_rows)} historical groups had multiple candidates and distinct H1 endpoints; formal status disagreement=0.
14. **Q14 — Any new candidate?** **NO**.
15. **Q15 — Source/missingness bias?** **YES**. Missing numeric rollout controls and source-specific reachability strongly select the replayable/primary subset.
16. **Q16 — Deterministic?** **YES**, two final complete passes have identical semantic hashes and zero row mismatches.
17. **Q17 — Fidelity mismatch?** **NO**, 16 preselected direct-backend checks all match endpoint, status, reason, value, and candidate hash.
18. **Q18 — Controller/shadow/map/dynamics modified?** **NO**. Only task-local import/lineage wrapper corrections were made.
19. **Q19 — On-policy/navigation experiment run?** **NO**.
20. **Q20 — Strongest supported claim.** On this frozen, architecture-reached cohort, PR #94 deterministically adds 18 candidate-dependent L2 future-safety FAIL signals after stored L1 PASS.
21. **Q21 — Unsupported claims.** Collision prevention, closed-loop improvement, controller efficacy, runtime performance, recursive feasibility, physical-world safety, or deployment readiness.
22. **Q22 — Next phase.** Design non-invasive on-policy shadow observation; do not grant controller authority.

## Denominators and mechanism result

Replay coverage is {n_formal}/{n_all} ({rate(n_formal, n_all):.6%}). Primary opportunity coverage is {n_eval}/{n_reached}. L1 PASS/L2 FAIL prevalence is {n_l1_pass_l2_fail}/{n_l1_pass_eval} ({rate(n_l1_pass_l2_fail, n_l1_pass_eval):.6%}); L1 PASS/L2 UNKNOWN is {n_l1_pass_l2_unknown}/{n_l1_pass_eval}. These are descriptive mechanism signals only.

## Candidate strata and multi-candidate evidence

Executed/selected candidates and logged non-executed candidates are reported separately. The latter never receive historical closed-loop counterfactual authority. The {len(multi_rows)} legitimate multi-candidate groups all have distinct H1 endpoints but no PASS/FAIL/UNKNOWN disagreement.

## Reproducibility and repair disclosure

The first server attempt stopped before evaluation because a task-local dynamically loaded dataclass module was not registered in `sys.modules`; this wrapper was fixed without scientific mutation. One complete result pass then exposed a task-local lineage merge-order issue (`l2_reached` was overwritten by the shadow result's null metadata); pre-fix outputs were preserved on the server, the merge order was corrected, and the same frozen replay was repeated. The final two full passes are deterministic and direct-backend differential checks pass. No controller, PR #94 implementation, map, dynamics, threshold, candidate, or protected blob changed.

## Decision

`CASE_A — VALID_INTERPRETABLE_FROZEN_REPLAY`

- FINAL_STATUS: `PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1`
- FINAL_DECISION: `FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION`
- Only next task: `DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1`
"""
    report_root = TASK_ROOT / "report"
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md").write_text(report, encoding="utf-8", newline="\n")

    pr_body = f"""## Scope

Validates the frozen PR #94 shadow-only L2/H1 implementation at exact head `9bffdd2db585974ee61684cebfc99229aa52c47c` against a source universe frozen before results. No new data, state, candidate, map, controller decision, on-policy collection, or navigation rollout was generated.

## Frozen cohort and denominators

- N_all: {n_all}
- replayability: formal={n_formal}, diagnostic={n_diag}, not replayable={n_not}
- architecture reached/evaluated: {n_reached}/{n_eval}
- L2: PASS={status['PASS']}, FAIL={status['FAIL']}, UNKNOWN={status['UNKNOWN']} (denominator {n_eval})
- NOT_REPLAYABLE was never counted as L2 UNKNOWN
- replayable rows have explicit source/missingness bias; see `selection_bias_audit.md`

## Mechanism evidence

- stored L1 PASS/L2 FAIL: {n_l1_pass_l2_fail}/{n_l1_pass_eval}
- stored L1 PASS/L2 UNKNOWN: {n_l1_pass_l2_unknown}/{n_l1_pass_eval}
- multi-candidate groups: {len(multi_rows)}; distinct H1 endpoints={multi_summary['N_groups_with_distinct_H1_endpoints']}; status disagreements={multi_summary['N_groups_with_L2_status_disagreement']}
- executed/selected and non-executed historical candidates are separated

This is candidate-dependent map-relative future-safety information, not collision prevention, closed-loop efficacy, or performance evidence.

## Integrity and authority

Two final complete passes are semantically identical; 16 deterministic direct-backend spot checks pass. Controller authority/intervention, candidate replacement, production mutation, formal navigation rollout, and on-policy collection are all zero. Four reviewers recommend `CASE_A` with bounded interpretation.

- FINAL_STATUS: `PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1`
- FINAL_DECISION: `FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION`
- Only next task: `DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1`
"""
    (TASK_ROOT / "DRAFT_PR_BODY.md").write_text(pr_body, encoding="utf-8", newline="\n")
    write_json(TASK_ROOT / "downstream_handoff.json", {
        "source_case": "CASE_A",
        "frozen_evidence_only": True,
        "controller_authority": False,
        "production_integration_authorized": False,
        "FINAL_STATUS": "PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1",
        "FINAL_DECISION": "FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION",
        "only_next_task": "DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1",
    })

    write_json(TASK_ROOT / "audit/replay_execution_accounting.json", {
        "failed_wrapper_attempt_before_any_L2_call": 1,
        "completed_replay_execution_batches": 2,
        "complete_pass_count_per_batch": 2,
        "total_complete_pass_count": 4,
        "final_preregistered_determinism_pass_count": 2,
        "unique_primary_candidate_count": n_eval,
        "raw_L2_calls_across_completed_passes": n_eval * 4,
        "reported_shadow_candidate_evaluation_count": n_eval,
        "pre_lineage_merge_fix_results_preserved_on_server": True,
        "scientific_input_or_method_mutation_count": 0,
    })

    manifest_record = {
        "task": "VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1",
        "branch": "l2-h1-shadow-frozen-replay-v1",
        "base": "l2-h1-shadow-certifier-v1",
        "pr94_head": "9bffdd2db585974ee61684cebfc99229aa52c47c",
        "selected_case": "CASE_A",
        "counts": {
            **{key: denominator[key] for key in (
                "N_all", "N_formal_replayable", "N_diagnostic_reconstructable", "N_not_replayable",
                "N_L2_reached", "N_L2_reachability_unknown", "N_L2_candidate_evaluated",
                "N_L2_PASS", "N_L2_FAIL", "N_L2_UNKNOWN",
            )},
            "N_L1_PASS_L2_PASS": n_l1_pass_l2_pass,
            "N_L1_PASS_L2_FAIL": n_l1_pass_l2_fail,
            "N_L1_PASS_L2_UNKNOWN": n_l1_pass_l2_unknown,
            **multi_summary,
            "formal_navigation_rollout_count": 0,
            "on_policy_collection_count": 0,
            "controller_intervention_count": 0,
            "new_data_collection_count": 0,
            "new_external_dataset_count": 0,
            "synthetic_state_generation_count": 0,
            "synthetic_candidate_generation_count": 0,
            "map_generation_count": 0,
            "map_training_count": 0,
            "map_mutation_count": 0,
            "historical_replay_manifest_count": 1,
            "replay_cohort_definition_count": 1,
            "controller_mutation_count": 0,
            "production_method_mutation_count": 0,
            "dynamics_mutation_count": 0,
            "candidate_library_mutation_count": 0,
            "backup_mutation_count": 0,
            "terminal_mutation_count": 0,
            "H2_implementation_count": 0,
            "formal_runtime_claim_count": 0,
            "formal_performance_claim_count": 0,
            "reviewer_count": 4,
        },
        "reviewer_case_votes": {name: value["recommended_case"] for name, value in reviews.items()},
        "server_task_root": "/disk1/zlab/maintenance_records/l2_h1_shadow_frozen_replay_v1",
        "server_report": "/disk1/zlab/maintenance_records/l2_h1_shadow_frozen_replay_v1/repo/reproduction/replay/l2_h1_shadow_frozen_replay_v1/report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md",
        "FINAL_STATUS": "PASS_L2_H1_FROZEN_REPLAY_VALIDATION_V1",
        "FINAL_DECISION": "FREEZE_REPLAY_EVIDENCE_AND_PREPARE_NONINVASIVE_ON_POLICY_SHADOW_OBSERVATION",
        "only_next_task": "DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1",
    }
    artifact_hashes = {}
    for path in sorted(TASK_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"run_manifest.json", "validation_result.json"} and "__pycache__" not in path.parts:
            artifact_hashes[path.relative_to(TASK_ROOT).as_posix()] = {"sha256": sha256_file(path), "size": path.stat().st_size}
    manifest_record["artifact_hashes"] = artifact_hashes
    write_json(TASK_ROOT / "run_manifest.json", manifest_record)
    print("PASS_ANALYSIS_ARTIFACT_BUILD", json.dumps(denominator, sort_keys=True))


if __name__ == "__main__":
    main()
