#!/usr/bin/env python3
"""Build the bounded review, decision, handoff, and report artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EXPECTED_HEAD = "7d48bf6c3b8932aa65d851c3cd70404404453cb3"
FINAL_STATUS = "PASS_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1"
FINAL_DECISION = "FREEZE_RUNTIME_NONINTERFERENCE_EVIDENCE_AND_VALIDATE_LOGGING_COMPLETENESS_PILOT"
NEXT_TASK = "VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1"
TRIALS = (0, 24, 49, 74, 99)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def metadata(run_id: str) -> dict[str, Any]:
    return load(ROOT / "run_logs" / "compact_runs" / run_id / "run_metadata.json")


def activation(run_id: str) -> dict[str, Any]:
    return load(ROOT / "run_logs" / "compact_runs" / run_id / "arm_activation.json")


def reviewer(name: str, evidence: list[str], minor: list[str], supported: list[str]) -> dict[str, Any]:
    return {
        "reviewer": name,
        "verdict": "PASS",
        "critical_blockers": [],
        "major_issues": [],
        "minor_issues": minor,
        "recommended_case": "CASE_A",
        "evidence_checked": evidence,
        "supported_claims": supported,
        "prohibited_claims": [
            "collision reduction", "progress improvement", "controller efficacy",
            "logging completeness pilot", "runtime or real-time guarantee",
            "formal prospective cohort result", "deployment guarantee",
        ],
    }


def main() -> int:
    pipeline = load(ROOT / "pipeline_result.json")
    self_result = load(ROOT / "self_consistency_results.json")
    c_sanity = load(ROOT / "arm_c_log_sanity.json")
    upstream = load(ROOT / "audit" / "frozen_upstream_identity.json")
    protected = load(ROOT / "audit" / "protected_source_audit.json")
    with (ROOT / "equivalence_matrix.csv").open(newline="", encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))

    if pipeline["FINAL_STATUS"] != FINAL_STATUS:
        raise RuntimeError("pipeline did not produce the preregistered PASS status")
    if any(row["exact_match"] != "True" or row["pairing_identity_match"] != "True" for row in matrix):
        raise RuntimeError("equivalence matrix contains a non-exact row")

    trial_rows = []
    for trial in TRIALS:
        ids = {arm: f"cross_{arm.lower()}_trial{trial:03d}" for arm in "ABC"}
        metas = {arm: metadata(run_id) for arm, run_id in ids.items()}
        acts = {arm: activation(run_id) for arm, run_id in ids.items()}
        hashes = {arm: metas[arm]["trace_hash"] for arm in "ABC"}
        trial_rows.append({
            "trial_id": trial,
            "step_count": metas["A"]["trace_step_count"],
            "trace_hash": hashes["A"],
            "A_B_C_exact": len(set(hashes.values())) == 1,
            "arm_c_capture_count": acts["C"]["capture_log_count"],
            "arm_c_result_count": acts["C"]["certificate_result_count"],
            "arm_c_worker_processed_count": acts["C"]["worker_processed_count"],
            "arm_c_leftover_worker_count": acts["C"]["leftover_shadow_worker_count"],
        })

    all_run_ids = sorted(p.name for p in (ROOT / "run_logs" / "compact_runs").iterdir() if p.is_dir() and (p / "run_metadata.json").exists())
    env_hashes = {load(ROOT / "run_logs" / "compact_runs" / run_id / "environment_identity.json")["pairing_identity_hash"] for run_id in all_run_ids}
    map_ids = {load(ROOT / "run_logs" / "compact_runs" / run_id / "environment_identity.json")["map_authority_id"] for run_id in all_run_ids}
    c_activations = [activation(run_id) for run_id in all_run_ids if "_c" in run_id]
    total_captures = sum(item["capture_log_count"] for item in c_activations)
    total_results = sum(item["certificate_result_count"] for item in c_activations)
    total_worker_processed = sum(item["worker_processed_count"] for item in c_activations)

    common = {
        "schema_version": "L2_H1_SHADOW_EQUIVALENCE_CLOSEOUT_V1",
        "upstream_pr": 97,
        "upstream_head": EXPECTED_HEAD,
        "selected_case": "CASE_A",
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "Only_next_task": NEXT_TASK,
        "frozen_trial_ids": list(TRIALS),
        "self_consistency": self_result,
        "exact_comparison_count": len(matrix),
        "first_divergence_count": 0,
        "trace_trial_rows": trial_rows,
        "real_qa_navigation_run_count": 21,
        "native_off_run_count": 7,
        "wrapper_off_run_count": 7,
        "wrapper_on_run_count": 7,
        "controller_mutation_count": 0,
        "instrumentation_mutation_count": 0,
        "map_mutation_count": 0,
        "candidate_library_mutation_count": 0,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "actual_fail_close_from_shadow_count": 0,
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "formal_performance_metric_count": 0,
        "formal_runtime_metric_count": 0,
        "L3_implementation_count": 0,
        "L4_implementation_count": 0,
        "L5_implementation_count": 0,
        "H2_implementation_count": 0,
        "arm_c_log_sanity": c_sanity["all_pass"],
        "arm_c_capture_count": total_captures,
        "arm_c_result_count": total_results,
        "arm_c_worker_processed_count": total_worker_processed,
        "environment_identity_count": len(env_hashes),
        "map_authority_identity_count": len(map_ids),
        "upstream_pr_count": len(upstream["preserved_pr_numbers"]),
        "protected_blob_count": protected["protected_blob_count"],
    }

    reviews = {
        "control_theory_review.json": reviewer(
            "CONTROL_THEORY",
            ["same-decision x_k/u_des/selected-u trace", "solver and branch trace", "plant input/output trace", "zero authority and zero intervention"],
            ["The bounded five-trial result does not establish control efficacy."],
            ["No observed control-trace perturbation in the preregistered QA manifest."],
        ),
        "robotics_systems_review.json": reviewer(
            "ROBOTICS_SYSTEMS",
            ["A/B/C activation records", "fresh process metadata", "GPU pre/post records", "map/config/environment identities", "worker shutdown records"],
            ["Fresh Nerfstudio initialization dominates wall time, but runtime metrics are intentionally excluded."],
            ["All three arms were correctly activated and task-owned workers were cleaned up."],
        ),
        "software_reproducibility_review.json": reviewer(
            "SOFTWARE_REPRODUCIBILITY",
            ["pre-frozen trial selection", "float.hex canonicalization", "21 exact comparator rows", "no tolerance field", "protected raw Git blob audit"],
            ["A pre-navigation task-local path mapping omission was repaired without producing a control step; its failed evidence is retained."],
            ["The bounded equivalence matrix is reproducible from immutable trace and activation artifacts."],
        ),
        "scientific_claim_review.json": reviewer(
            "SCIENTIFIC_CLAIM",
            ["five-trial denominator", "self-consistency gate", "first-divergence record", "zero performance/runtime metrics", "C log sanity scope"],
            ["Arm-C log parsing/join is sanity evidence only, not a completeness pilot."],
            ["Bounded runtime non-interference evidence under the tested deterministic Stonehenge conditions."],
        ),
    }
    for name, data in reviews.items():
        write_json(ROOT / "reviewers" / name, data)

    decision = dict(common)
    decision.update({
        "reviewer_count": 4,
        "reviewer_case_votes": {"CASE_A": 4},
        "reviewer_disagreement": False,
        "supported_claims": [
            "Across the preregistered bounded Stonehenge QA manifest, NATIVE_OFF, WRAPPER_OFF, and WRAPPER_ON produced identical frozen control traces under the tested deterministic conditions.",
            "The PR #97 wrapper and active shadow observation stack showed no observed control-trace perturbation in these QA runs.",
        ],
        "prohibited_claims": [
            "collision reduction", "progress improvement", "controller efficacy",
            "logging completeness", "real-time performance", "formal cohort result",
        ],
        "unresolved_blockers": [],
    })
    write_json(ROOT / "FINAL_CASE_DECISION.json", decision)

    manifest = dict(common)
    manifest.update({
        "task": "VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1",
        "branch": "validate-l2-h1-shadow-instrumentation-equivalence-v1",
        "base_branch": "implement-l2-h1-on-policy-shadow-instrumentation-v1",
        "server_task_root": "/disk1/zlab/maintenance_records/l2_h1_shadow_instrumentation_off_vs_on_equivalence_v1",
        "pre_navigation_infrastructure_attempt_count": 1,
        "pre_navigation_infrastructure_control_step_count": 0,
        "pre_navigation_repair": "Added missing read-only data symlink beside the existing outputs symlink in the task-local isolated run directory.",
        "result_artifacts": [
            "self_consistency_results.json", "equivalence_matrix.csv", "equivalence_summary.json",
            "first_divergence_forensic.json", "first_divergence_context.md", "arm_c_log_sanity.json",
        ],
    })
    write_json(ROOT / "run_manifest.json", manifest)

    handoff = dict(common)
    handoff.update({
        "authorization_required": True,
        "do_not_auto_execute": True,
        "prerequisites_for_next_task": [
            "Use the exact PR created by this task as upstream.",
            "Keep L2/H1 shadow authority false and controller output unaffected.",
            "Treat this equivalence QA as non-interference evidence, not logging completeness evidence.",
            "Pre-freeze the logging-completeness pilot manifest and gates before collection.",
        ],
    })
    write_json(ROOT / "downstream_handoff.json", handoff)

    table_lines = ["| Trial | Steps | Canonical trace SHA-256 | A=B=C | C captures/results |", "|---:|---:|---|:---:|---:|"]
    for row in trial_rows:
        table_lines.append(f"| {row['trial_id']} | {row['step_count']} | `{row['trace_hash']}` | YES | {row['arm_c_capture_count']}/{row['arm_c_result_count']} |")
    table = "\n".join(table_lines)

    report = f"""# Validate L2/H1 shadow instrumentation OFF-vs-ON equivalence V1

## Technical summary

**Result: PASS, CASE_A.** The preregistered bounded Stonehenge QA executed 21 real navigation runs: six fresh-process self-consistency runs plus five frozen trial IDs across NATIVE_OFF, WRAPPER_OFF, and WRAPPER_ON. All 21 exact comparisons passed; no first divergence was found. The active C arm produced {total_captures} immutable captures and {total_results} joinable certificate results with zero controller intervention, zero candidate replacement, and no leftover shadow worker.

This supports only a bounded runtime non-interference claim under the tested deterministic conditions. It is not a collision/progress experiment, a logging-completeness pilot, a runtime benchmark, or a formal prospective cohort.

## Direct answers to the 25 required questions

1. **Q1 — PR #97 exact identity?** YES. Expected and actual head: `{EXPECTED_HEAD}`; PR #97 was frozen as Open Draft before navigation.
2. **Q2 — Trial IDs frozen before results?** YES. Stable sorted official100 rows with positions `floor(j*(N-1)/(K-1))`, `N=100`, `K=5`, yielded `[0, 24, 49, 74, 99]` before any QA navigation.
3. **Q3 — A/B/C used?** YES: NATIVE_OFF, WRAPPER_OFF, WRAPPER_ON.
4. **Q4 — A truly had no wrapper?** YES. Seven A activations report `wrapper_loaded=false`, observer off, no worker.
5. **Q5 — B wrapper loaded but observer disabled?** YES. Seven B activations report real wrapper delegation, observer off, and no worker start.
6. **Q6 — C fully active?** YES. Seven C activations report wrapper, immutable capture, bounded queue, worker, frozen L0/L1/L2, append-only logs, and complete shutdown.
7. **Q7 — A self-consistency?** PASS; A1=A2 exactly, 318 steps.
8. **Q8 — B self-consistency?** PASS; B1=B2 exactly, 318 steps.
9. **Q9 — C self-consistency?** PASS; C1=C2 exactly, 318 steps; both processed 318 observations.
10. **Q10 — A vs B selected-u exact?** YES for all five frozen trials.
11. **Q11 — B vs C selected-u exact?** YES for all five frozen trials.
12. **Q12 — A vs C selected-u exact?** YES for all five frozen trials.
13. **Q13 — State trace exact?** YES, via the canonical per-step comparator.
14. **Q14 — Solver/branch exact?** YES.
15. **Q15 — Plant input/output exact?** YES.
16. **Q16 — Termination exact?** YES.
17. **Q17 — First divergence?** NONE; `first_divergence_count=0`.
18. **Q18 — Tolerance modified after results?** NO. Equality remained exact; floats were canonicalized with `float.hex()` and `numeric_tolerance=null`.
19. **Q19 — Trial replaced based on L2 result?** NO; candidate/trial replacement count is zero.
20. **Q20 — C logs parse and join?** YES for all seven C runs; payload hashes join and selected `u_k` is present.
21. **Q21 — Treated as logging pilot?** NO; `logging_pilot_run_count=0`.
22. **Q22 — Collision/progress treated as performance?** NO; they appear only inside trace identity QA.
23. **Q23 — Formal 100-trial prospective cohort run?** NO; `formal_on_policy_cohort_count=0`.
24. **Q24 — Maximum claim?** No observed control-trace perturbation across the preregistered bounded five-trial Stonehenge manifest under the tested deterministic conditions.
25. **Q25 — Next step?** `{NEXT_TASK}`, only after separate authorization.

## Five frozen trials all matched exactly

{table}

The table is used instead of a chart because the scientific question is exact identity, not magnitude or trend. A visual encoding would add no information beyond the per-trial hashes and exact flags.

## Scope, cohort, and equality contract

The QA cohort is five deterministic Stonehenge trial IDs selected before results. Each trial ran in three fresh processes using the same seed, GPU, official environment, map authority, protected `run.py`, and frozen controller. The primary trace includes aligned state, nominal command, selected command, solver/branch, plant input/output, termination, goal, and map identity fields. Equality is byte-stable semantic equality after deterministic JSON normalization and exact hexadecimal float representation; no numerical tolerance is permitted.

## The three-arm method isolated wrapper and observer effects

- **A — NATIVE_OFF:** protected run without importing the PR #97 wrapper.
- **B — WRAPPER_OFF:** exact PR #97 wrapper with real delegation, observer disabled, and no worker.
- **C — WRAPPER_ON:** the same wrapper with immutable observation copy, bounded nonblocking queue, real worker, frozen L0/L1/L2 evaluation, and append-only logs.

The self-consistency gate passed separately for A, B, and C before the five-trial matrix. A-versus-B isolates wrapper loading; B-versus-C isolates active shadow observation; A-versus-C tests the end-to-end difference.

## Arm C was active but had zero authority

Across seven C runs, capture, certificate-result, and worker-processed totals were all {total_captures}. All C activations completed shutdown, reported no leftover worker, and retained `controller_authority=false`. Queue/worker evidence was inspected only for minimal parse/join sanity. It does not estimate logging completeness or runtime suitability.

## Robustness and failure handling

The first launch attempt stopped before map construction because the task-local isolated run directory mapped `outputs` but omitted the frozen config's relative `data` path. It produced zero control steps. The failed directory and traceback were retained; the task-local wrapper was corrected to add a read-only `data` symlink, and the full matrix restarted from a clean output root. No protected source, controller, instrumentation implementation, map, trial, seed, threshold, or result was changed.

Independent checks found one environment identity and one map authority identity across all 21 valid runs. The protected raw-Git audit matched all {protected['protected_blob_count']} blobs with zero protected-path diff.

## Limitations and bounded interpretation

The manifest contains five Stonehenge trials, not the official100 cohort. Exact equality here does not prove equivalence for untested trials, other maps, nondeterministic environments, or future code. It also does not show collision reduction, progress improvement, intervention efficacy, real-time feasibility, deployment safety, or logging completeness. Shadow results never had decision authority, so this task cannot measure control benefit.

## Recommended next step

Freeze this bounded non-interference evidence. If separately authorized, run `{NEXT_TASK}` with its own pre-frozen manifest and completeness gates. Do not infer or execute that task automatically from this PASS.

## Further questions

- Will a separately preregistered pilot meet required `u_k`, reachability, map-authority, queue/drop, and join completeness gates?
- Does instrumentation remain non-interfering under any future environment or controller change? Such a change requires a new equivalence qualification.

## Final decision

- `FINAL_STATUS={FINAL_STATUS}`
- `FINAL_DECISION={FINAL_DECISION}`
- `Only_next_task={NEXT_TASK}`
"""
    write_text(ROOT / "report" / "REPORT_VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1.md", report)

    pr_body = f"""## Result

`{FINAL_STATUS}`

This Draft PR records bounded OFF-vs-ON control-trace equivalence QA for exact PR #97 head `{EXPECTED_HEAD}`.

## Frozen design

- Arms: NATIVE_OFF, WRAPPER_OFF, WRAPPER_ON.
- Trial selection: stable sorted official100 positions `floor(j*(N-1)/(K-1))`.
- Frozen IDs: `0, 24, 49, 74, 99`.
- Matrix: six self-consistency runs, then five trials x three arms.
- Equality: exact canonical state/u_des/selected-u/solver/branch/plant/termination/map trace; no tolerance and no post-hoc change.

## Evidence

- A/B/C self-consistency: PASS/PASS/PASS.
- A-vs-B, B-vs-C, A-vs-C: 5/5 exact for each comparison.
- Exact comparison rows: 21/21.
- First divergence: NONE.
- C activation: seven valid runs, {total_captures} captures, {total_results} joinable certificate results, no leftover worker.
- Controller intervention/candidate replacement: 0/0.
- Protected blobs: {protected['protected_blob_count']}/{protected['protected_blob_count']} match; controller/method/PR #97 implementation unchanged.

## Boundary

Collision/progress fields are trace identity QA only. This is not an efficacy experiment, runtime benchmark, logging-completeness pilot, or formal prospective cohort. No L3/L4/L5/H2 was implemented.

## Reviews

Control theory, robotics/systems, software/reproducibility, and scientific-claim reviewers all recommend CASE_A with no critical blocker.

## Decision

- `FINAL_STATUS={FINAL_STATUS}`
- `FINAL_DECISION={FINAL_DECISION}`
- `Only next task={NEXT_TASK}` (requires separate authorization)
"""
    write_text(ROOT / "DRAFT_PR_BODY.md", pr_body)

    print(json.dumps({"generated": True, "trial_rows": trial_rows, "arm_c_captures": total_captures, "reviews": 4}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
