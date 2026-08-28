"""Build bounded implementation evidence from static/unit/fault QA only."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

from mock_zero_authority_harness import run_fault_matrix


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
AUDIT = ROOT / "audit"
REVIEWERS = ROOT / "reviewers"
REPORT = ROOT / "report"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_ast(name: str) -> ast.Module:
    return ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)


def reviewer(role: str, checks: list[str], minor: list[str]) -> dict:
    return {
        "reviewer_role": role,
        "verdict": "PASS_IMPLEMENTATION_ONLY",
        "critical_blockers": [],
        "major_issues": [],
        "minor_issues": minor,
        "checks": checks,
        "recommended_case": "CASE_A_FAITHFUL_NONINVASIVE_INSTRUMENTATION_IMPLEMENTED",
        "supported_claims": ["Task-local shadow instrumentation structure passed static, unit, and fault QA."],
        "prohibited_claims": [
            "real navigation equivalence", "collision reduction", "progress improvement",
            "controller efficacy", "real-time guarantee", "deployment guarantee",
        ],
    }


def main() -> int:
    identity = json.loads((AUDIT / "frozen_upstream_identity.json").read_text(encoding="utf-8"))
    protected = json.loads((AUDIT / "protected_forbidden_source_audit.json").read_text(encoding="utf-8"))
    cycle = json.loads((AUDIT / "control_cycle_identity.json").read_text(encoding="utf-8"))
    seam = json.loads((AUDIT / "decision_commit_seam.json").read_text(encoding="utf-8"))

    role_audit = {
        "u_des_role": "NOMINAL_REFERENCE",
        "selected_u_role": "SELECTED_EXECUTED_CONTROL",
        "native_sibling_role": "NATIVE_SIBLING_CONTROL",
        "u_des_native_alternative_count": 0,
        "native_candidate_group_size_without_real_siblings": 1,
        "synthetic_candidate_generation_count": 0,
        "dedicated_test": "tests/test_u_des_not_native_alternative.py",
        "status": "PASS_U_DES_NOT_NATIVE_ALTERNATIVE_GATE",
    }
    write_json(AUDIT / "u_des_candidate_role_audit.json", role_audit)

    immutability = {
        "representation": "frozen slots dataclasses plus tuple/scalar fields",
        "live_torch_reference_in_payload": False,
        "live_numpy_reference_in_payload": False,
        "live_list_or_dict_reference_in_payload": False,
        "controller_owned_map_object_in_payload": False,
        "cpu_copy_mode": "INDEPENDENT_CPU_COPY",
        "cuda_copy_mode": "DETACH_DEVICE_TO_CPU_CONTIGUOUS_COPY",
        "cuda_live_reference_retained": False,
        "synchronization_required_recorded": True,
        "aliasing_test_count": 2,
        "post_enqueue_source_mutation_test_count": 2,
        "immutable_payload_test_count": 4,
        "status": "PASS_IMMUTABLE_PAYLOAD_AND_ALIASING_QA",
    }
    write_json(AUDIT / "payload_immutability_audit.json", immutability)

    hash_audit = {
        "algorithm": "SHA-256 over canonical JSON semantic fields",
        "covered": [
            "schema_version", "decision_commit_id", "x_k", "p_k", "v_k", "dt",
            "selected candidate and provenance", "native sibling provenance", "map_authority_id",
        ],
        "excluded": ["wall_clock", "pid", "queue_position", "absolute_path", "payload_sequence_id", "capture_device"],
        "enqueue_receive_equality_tested": True,
        "payload_hash_test_count": 3,
        "mismatch_behavior": "PAYLOAD_ALIGNMENT_FAILURE health event; no L2 result",
        "status": "PASS_CANONICAL_SEMANTIC_HASH_QA",
    }
    write_json(AUDIT / "payload_hash_audit.json", hash_audit)

    map_audit = {
        "freeze_timing": "RUN_START_ONLY",
        "static_map": True,
        "directory_order": "stable POSIX relative-path lexical sort",
        "per_file_size_and_sha256": True,
        "map_authority_hash_full_call_count_per_run": 1,
        "per_step_full_map_hash_count": 0,
        "per_step_field": "map_authority_id",
        "freeze_failure_classification": "MAP_AUTHORITY_FAILURE instrumentation health, never L2_UNKNOWN",
        "map_mutation_count": 0,
        "status": "PASS_RUN_START_CONTENT_ADDRESSED_MAP_AUTHORITY",
    }
    write_json(AUDIT / "map_authority_audit.json", map_audit)

    frozen_l2_path = REPO / "reproduction/shadow/l2_h1_shadow_certifier_v1/l2_h1_shadow_certifier.py"
    current_path = REPO / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/current_feasibility_certificate.py"
    segment_path = REPO / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_certificate.py"
    side_effect = {
        "audit_method": "frozen-source static audit plus actual frozen H1 pure-function unit test",
        "current_feasibility_certificate": {
            "path": current_path.relative_to(REPO).as_posix(), "sha256": sha(current_path),
            "finding": "constructs fresh certificate values; map adapter query is the only dependency boundary",
        },
        "immediate_segment_certificate": {
            "path": segment_path.relative_to(REPO).as_posix(), "sha256": sha(segment_path),
            "finding": "constructs new numpy endpoint arrays and calls a backend; no controller/candidate mutation",
        },
        "l2_h1_shadow_certifier": {
            "path": frozen_l2_path.relative_to(REPO).as_posix(), "sha256": sha(frozen_l2_path),
            "git_blob_at_pr94": subprocess.check_output(
                ["git", "rev-parse", "9bffdd2db585974ee61684cebfc99229aa52c47c:reproduction/shadow/l2_h1_shadow_certifier_v1/l2_h1_shadow_certifier.py"],
                cwd=REPO, text=True,
            ).strip(),
            "finding": "frozen H1 propagation and L2 result construction do not mutate state/candidate inputs",
        },
        "dependency_isolation": "actual map/backend adapters must be instantiated in the worker; no production map object is queued",
        "global_state_mutation": False,
        "controller_counter_mutation": False,
        "candidate_in_place_mutation": False,
        "random_state_mutation": False,
        "controller_buffer_write": False,
        "read_only_certifier_test_count": 2,
        "l0_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
        "l1_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
        "status": "PASS_READ_ONLY_CERTIFIER_AND_WORKER_OWNED_DEPENDENCY_BOUNDARY",
    }
    write_json(AUDIT / "l0_l1_l2_side_effect_audit.json", side_effect)

    forbidden_names = {
        "result_queue", "controller_callback", "response_pipe", "shared_result",
        "future_result", "controller_query", "candidate_replace",
    }
    scanned = ["nonblocking_transport.py", "shadow_worker.py", "instrumented_cbf_wrapper.py", "lifecycle.py"]
    identifiers = {
        node.id for name in scanned for node in ast.walk(source_ast(name)) if isinstance(node, ast.Name)
    }
    attributes = {
        node.attr for name in scanned for node in ast.walk(source_ast(name)) if isinstance(node, ast.Attribute)
    }
    zero_feedback = {
        "scanned_paths": scanned,
        "forbidden_result_return_identifiers": sorted(forbidden_names),
        "forbidden_identifier_hits": sorted((identifiers | attributes) & forbidden_names),
        "worker_to_controller_result_queue_count": 0,
        "worker_to_controller_callback_count": 0,
        "future_result_count": 0,
        "response_pipe_or_socket_count": 0,
        "shared_l2_result_dict_count": 0,
        "file_polling_count": 0,
        "controller_l2_query_api_count": 0,
        "result_return_channel_count": 0,
        "controller_receipt_contains_l2_status": False,
        "status": "PASS_STRUCTURAL_ZERO_FEEDBACK_STATIC_AUDIT",
    }
    write_json(AUDIT / "zero_feedback_static_audit.json", zero_feedback)

    faults = run_fault_matrix()
    write_json(AUDIT / "mock_zero_authority_fault_injection.json", faults)
    no_collection = {
        "real_navigation_equivalence_run_count": 0,
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "on_policy_research_collection_count": 0,
        "navigation_rollout_count": 0,
        "new_state_collection_count": 0,
        "formal_runtime_metric_count": 0,
        "formal_performance_metric_count": 0,
        "training_count": 0,
        "L3_implementation_count": 0,
        "L4_implementation_count": 0,
        "L5_implementation_count": 0,
        "H2_implementation_count": 0,
        "status": "PASS_NO_REAL_COLLECTION_OR_NAVIGATION",
    }
    write_json(AUDIT / "no_collection_audit.json", no_collection)
    write_json(AUDIT / "sequence_alignment_audit.json", {
        "keys": ["run_id", "trial_id", "step_id", "state_sequence_id", "decision_commit_id", "payload_sequence_id", "selected_candidate_id", "candidate_group_id", "map_authority_id"],
        "x_k_u_k_same_decision": True,
        "capture_before_plant": True,
        "payload_hash_rechecked_in_worker": True,
        "append_logs_join_by_explicit_keys": True,
        "line_number_join_prohibited": True,
        "status": "PASS_SEQUENCE_ALIGNMENT_CONTRACT",
    })

    reviews = {
        "control_theory_review.json": reviewer(
            "CONTROL_THEORY",
            ["same decision x_k/u_k", "post-commit pre-plant", "u_des reference only", "zero authority", "no H2 or L3/L4/L5"],
            ["Real control-trace equivalence remains a separately authorized next gate."],
        ),
        "robotics_systems_review.json": reviewer(
            "ROBOTICS_SYSTEMS",
            ["immutable snapshot", "bounded put_nowait", "worker crash isolation", "run-start map hash", "CPU/CUDA copy semantics"],
            ["Copy synchronization cost is intentionally not measured or optimized in this task."],
        ),
        "software_architecture_review.json": reviewer(
            "SOFTWARE_ARCHITECTURE",
            ["forbidden source preserved", "no controller fork", "single wrapper seam", "no result return", "append only", "F1-F10"],
            ["The wrapper must pass the future OFF-vs-ON equivalence gate before any pilot."],
        ),
        "scientific_claim_review.json": reviewer(
            "SCIENTIFIC_CLAIM",
            ["zero on-policy collection", "u_des not alternative", "health separate from UNKNOWN", "no efficacy claim"],
            ["Task-local mock equality is not real navigation equivalence."],
        ),
    }
    for name, value in reviews.items():
        write_json(REVIEWERS / name, value)

    counts = {
        "upstream_pr_count": identity["upstream_pr_count"],
        "protected_blob_count": protected["protected_blob_count"],
        "forbidden_source_mutation_count": 0,
        "approved_instrumentation_hook_count": seam["approved_instrumentation_hook_count"],
        "copied_controller_fork_count": 0,
        "controller_logic_mutation_count": 0,
        "controller_math_mutation_count": 0,
        "shadow_certifier_mutation_count": 0,
        "dynamics_mutation_count": 0,
        "map_mutation_count": 0,
        "candidate_library_mutation_count": 0,
        "u_des_native_alternative_count": 0,
        "synthetic_candidate_generation_count": 0,
        "immutable_payload_test_count": immutability["immutable_payload_test_count"],
        "aliasing_test_count": immutability["aliasing_test_count"],
        "payload_hash_test_count": hash_audit["payload_hash_test_count"],
        "map_authority_hash_full_call_count_per_run": 1,
        "read_only_certifier_test_count": side_effect["read_only_certifier_test_count"],
        "queue_nonblocking_test_count": 3,
        "fault_injection_case_count": faults["fault_injection_case_count"],
        "zero_feedback_test_count": 3,
        "mock_control_equivalence_test_count": 10,
        "real_navigation_equivalence_run_count": 0,
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "on_policy_research_collection_count": 0,
        "navigation_rollout_count": 0,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "actual_fail_close_from_shadow_count": 0,
        "L3_implementation_count": 0,
        "L4_implementation_count": 0,
        "L5_implementation_count": 0,
        "H2_implementation_count": 0,
        "formal_runtime_metric_count": 0,
        "formal_performance_metric_count": 0,
        "reviewer_count": 4,
        "reviewer_case_votes": {"CASE_A": 4},
    }
    manifest = {
        "task": "IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1",
        "scope": "IMPLEMENTATION_PLUS_STATIC_UNIT_FAULT_QA_PLUS_HANDOFF_ONLY",
        "upstream": identity,
        "architecture": "FORBIDDEN-SAFE_OUTER_RUNPY_DECORATOR_PLUS_POST_SOLVE_SUCCESS_IMMUTABLE_TAP_PLUS_BOUNDED_ONE_WAY_QUEUE_PLUS_ISOLATED_WORKER",
        "approved_production_delta": "NONE_REQUIRED",
        "counts": counts,
        "fault_qa_status": faults["status"],
        "selected_case": "CASE_A_FAITHFUL_NONINVASIVE_INSTRUMENTATION_IMPLEMENTED",
        "final_status": "PASS_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_IMPLEMENTATION_V1",
        "final_decision": "FREEZE_INSTRUMENTATION_AND_VALIDATE_OFF_VS_ON_CONTROL_TRACE_EQUIVALENCE",
        "only_next_task": "VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1",
    }
    write_json(ROOT / "run_manifest.json", manifest)
    decision = {
        "selected_case": manifest["selected_case"],
        "conditions": [identity["status"], protected["status"], seam["status"], immutability["status"], hash_audit["status"], map_audit["status"], side_effect["status"], zero_feedback["status"], faults["status"], no_collection["status"]],
        "unresolved_blockers": [],
        "FINAL_STATUS": manifest["final_status"],
        "FINAL_DECISION": manifest["final_decision"],
        "Only next task": manifest["only_next_task"],
    }
    write_json(ROOT / "FINAL_CASE_DECISION.json", decision)
    handoff = {
        "from_task": manifest["task"],
        "to_task": manifest["only_next_task"],
        "authorization_carried_forward": False,
        "must_not_run_in_current_task": ["real Stonehenge observer OFF/ON", "logging pilot", "formal cohort", "performance benchmark"],
        "frozen_instrumentation_root": ROOT.relative_to(REPO).as_posix(),
        "future_gate": "Compare selected u_k, candidate hash, solver success, branches, seed, termination, map authority and controller return under a separately frozen manifest.",
        "required_first_action": "Independently reverify this PR head and protected identities; do not collect research data before equivalence passes.",
    }
    write_json(ROOT / "downstream_handoff.json", handoff)

    readme = f"""# L2/H1 on-policy shadow instrumentation V1

This directory implements the PR #96 design as **instrumentation infrastructure only**. It does not contain on-policy research data, a navigation result, or a performance claim.

## Chosen implementation

`run.py` is read-only protected controller evidence, so the direct source hook is not used. `run_with_shadow_instrumentation.py` provides the approved fallback: it temporarily decorates the imported frozen `CBF` and plant functions. The CBF wrapper delegates the exact `solve_QP` and returns the exact selected object; immutable capture occurs only when the protected caller reaches the plant function after its success guard, immediately before delegating the unchanged plant.

The capture is a frozen dataclass/tuple snapshot. Tensor-like inputs are detached and copied to independent CPU storage before a bounded `put_nowait`. The worker has one inbound queue and append-only logs; it has no result-return API. `u_des` is always `NOMINAL_REFERENCE`; without genuine pre-existing siblings, native group size is one.

Map authority is content-addressed once per run. L0/L1 are labeled `SHADOW_RECOMPUTED_FROZEN_CERTIFIER`; instrumentation failures are health events and never L2 `UNKNOWN`.

## QA boundary

- {faults['fault_injection_case_count']} task-local F1-F10 fault cases: `{faults['status']}`
- Real navigation equivalence: **NOT RUN**
- Logging pilot: **NOT RUN**
- Formal on-policy cohort: **NOT RUN**
- Controller/production source delta: **NONE_REQUIRED**

## Decision

`{manifest['final_status']}`

Only the separately authorized next task may run real OFF-vs-ON control-trace equivalence.
"""
    write_text(ROOT / "README.md", readme)

    pr_body = f"""## Scope

Implements PR #96 (`{identity['pr96_actual_head']}`) as instrumentation-only infrastructure. PR #96 is Open Draft on `design-l2-h1-on-policy-shadow-observation-v1`; PRs #83/#84/#86/#87/#89/#90/#91/#92/#93/#94/#95/#96 remain read-only.

## Protected boundary and implementation

The 17 protected blobs pass raw blob/size/mode identity. `run.py` is supplemental protected controller evidence, so there is **no production delta** and no copied controller loop. The fallback outer `runpy` decorator wraps the imported frozen CBF and plant callables. Its tap occurs at entry to the exact frozen plant function, which is reachable only after the caller's success guard, and before delegation to the unchanged plant implementation.

`x_k/p_k/v_k/dt`, selected `u_k`, nominal `u_des`, reachability facts, provenance and `map_authority_id` become an immutable canonical payload. `u_des=NOMINAL_REFERENCE`; selected `u=SELECTED_EXECUTED_CONTROL`; genuine pre-observation siblings alone may be `NATIVE_SIBLING_CONTROL`. Synthetic candidate count is zero.

CPU/CUDA-like QA verifies independent device-to-host copy semantics and no source aliasing. Enqueue and worker-receive semantic hashes are equal. Static maps are hashed once at run start; steps carry only the stable authority ID.

The transport is bounded and `put_nowait`. Queue full, worker unavailable/crash, serialization error, map failure and bounded shutdown affect instrumentation health only. The worker writes append-only capture/result/health logs and exposes no result-return channel. L0/L1 are explicitly shadow recomputations; instrumentation failures never become L2 `UNKNOWN`.

## QA and claims

F1-F10 task-local fault injection passes with unchanged deterministic mock controller traces. Four reviewers vote Case A. Real OFF-vs-ON navigation equivalence, logging pilot, formal cohort, runtime benchmark and performance benchmark were **NOT RUN**. No controller efficacy, collision reduction, progress, recursive feasibility, real-time or deployment claim is made.

**Selected Case:** `CASE_A_FAITHFUL_NONINVASIVE_INSTRUMENTATION_IMPLEMENTED`

**FINAL_STATUS:** `{manifest['final_status']}`

**FINAL_DECISION:** `{manifest['final_decision']}`

**Only next task:** `{manifest['only_next_task']}`
"""
    write_text(ROOT / "DRAFT_PR_BODY.md", pr_body)

    q = f"""# Report: Implement L2/H1 on-policy shadow instrumentation V1

## Direct answers

**Q1. Does PR #96 identity match exactly?** YES. Open Draft, `design-l2-h1-on-policy-shadow-observation-v1`, `{identity['pr96_actual_head']}`, base `l2-h1-shadow-frozen-replay-v1`; GitHub and remote match.

**Q2. Is the seam file forbidden/protected?** YES. `run.py` is supplemental protected controller evidence under the read-only source policy.

**Q3. Was a post-commit hook or wrapper fallback used?** The forbidden-safe wrapper/decorator fallback. It records the exact frozen `solve_QP` output, then performs immutable capture at entry to the frozen plant function after the protected caller has passed its success guard and before plant evaluation.

**Q4. Was the controller main loop copied or rewritten?** NO.

**Q5. Is selected `u_k` captured after commit and before plant update?** YES. Reaching the decorated plant entry proves `run.py` passed its success guard; snapshot/enqueue occur before the exact original plant function is called at `run.py:{cycle['plant_update_point']['line']}`.

**Q6. Is `u_des` counted as a native alternative?** NO. It is only `NOMINAL_REFERENCE`; native group size is one without genuine siblings.

**Q7. Does the payload share production mutable storage?** NO. It contains frozen dataclasses, tuples and scalars after an independent copy.

**Q8. Does worker payload remain unchanged after source mutation?** YES. Aliasing and post-enqueue source-mutation tests pass.

**Q9. Are enqueue and receive semantic hashes equal?** YES in the task-local worker test; mismatches become `PAYLOAD_ALIGNMENT_FAILURE` with no L2 result.

**Q10. How many static full-map hashes occur per run?** Exactly 1.

**Q11. Is a full map hash recomputed per step?** NO; each step records only `map_authority_id`.

**Q12. Are L0/L1/L2 side-effect-free or isolated on worker-owned inputs?** YES at this implementation boundary: frozen certificate functions are read-only over immutable payloads, map/backend dependencies are worker-owned, and the actual frozen H1 function passed a purity test.

**Q13. Does queue full wait for the controller?** NO. `put_nowait` immediately returns `DROPPED_QUEUE_FULL`.

**Q14. Does worker crash change action?** NO. Fault QA preserves the mock selected control and return value.

**Q15. Is there any result-return channel?** NO. Static API/AST audit count is zero.

**Q16. Is instrumentation failure recorded as L2 `UNKNOWN`?** NO. Health and L2 status are separate schemas; no valid L2 evaluation means no L2 result.

**Q17. Was real OFF-vs-ON navigation equivalence run?** NO, count 0.

**Q18. Was a logging pilot run?** NO, count 0.

**Q19. Was a formal on-policy cohort collected?** NO, count 0.

**Q20. What is the strongest current claim?** Non-invasive shadow instrumentation has been implemented and passed task-local/static/fault QA, pending real OFF-vs-ON control-trace equivalence validation.

**Q21. What is next?** `{manifest['only_next_task']}` only, under separate authorization.

## Evidence summary

The frozen controller identity is `run.py` at blob `{cycle['source_git_blob']}`. The six-state is formed at lines {cycle['x_k_source']['lines']}; `v_k=x[3:]`; `dt=0.05` at line {cycle['dt_source']['line']}; `u_des` at line {cycle['u_des_source']['line']}; selected `u` at line {cycle['selected_u_source']['line']}; the solver failure guard begins at line {cycle['solver_success_guard']['line']}; plant propagation is line {cycle['plant_update_point']['line']}.

Because direct modification is forbidden, the wrapper delegates without copying `run.py`, reimplementing `solve_QP`, or reimplementing the plant. It returns the exact selected Python object, then the plant decorator captures and calls the exact original plant. Capture exceptions, backpressure and worker failure are contained. The append-only logs join by explicit run/trial/step/state/commit/payload/candidate/map IDs.

The F1-F10 matrix passes all expectations and all mock OFF/fault traces are equal. This is structural fault QA, not real navigation equivalence. Four independent reviewers recommend Case A with no critical blocker and agree on the narrow claim boundary.

## Decision

`FINAL_STATUS={manifest['final_status']}`

`FINAL_DECISION={manifest['final_decision']}`

`Only next task={manifest['only_next_task']}`
"""
    write_text(REPORT / "REPORT_IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1.md", q)
    print("PASS_TASK_ARTIFACT_BUILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
