# L2/H1 On-Policy Shadow Instrumentation V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan task-by-task in the current authorized session. Subagent delegation is not authorized. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a post-commit, pre-plant, immutable, nonblocking, zero-feedback shadow instrumentation layer and prove its structural behavior with task-local static/unit/fault QA only.

**Architecture:** `run.py` is a protected supplemental source, so the implementation uses the PR #96 wrapper/decorator fallback without copying or editing the controller. A wrapper intercepts the already-produced successful `CBF.solve_QP` return, deep-copies the same-decision state/nominal reference/selected control into an immutable payload, and sends it through a bounded `put_nowait` transport to an isolated append-only worker with no result channel.

**Tech Stack:** Python 3 standard library, frozen dataclasses/tuples, canonical JSON/SHA-256, `queue.Queue`, `threading`, JSON Lines, JSON Schema, unittest, pytest, AST/static Git audits.

---

### Task 1: Freeze upstream and forbidden-source boundary

**Files:**
- Create: `freeze_inputs.py`
- Create: `audit/frozen_upstream_identity.json`
- Create: `audit/protected_forbidden_source_audit.json`
- Create: `audit/control_cycle_identity.json`
- Create: `audit/decision_commit_seam.json`
- Create: `audit/approved_production_delta.json`

- [ ] Verify PR #96 is Open Draft at `1783aff5f6d221efc26d34f8b47b966e2d9eee3e`, and preserve PRs #83-#96.
- [ ] Recompute raw Git blob, byte size, and mode for the 17 protected records and all supplemental protected records.
- [ ] Record that `run.py` is supplemental protected source and cannot be patched.
- [ ] Approve `NONE_REQUIRED` production delta and the wrapper/decorator fallback only.
- [ ] Record exact frozen `x`, `v`, `dt`, `u_des`, `u`, success guard, commit condition, and plant-update source locations.

### Task 2: Implement immutable evidence model

**Files:**
- Create: `canonical_hash.py`
- Create: `immutable_payload.py`
- Create: `candidate_provenance.py`
- Create: `reachability_capture.py`
- Test: `tests/test_immutable_payload.py`
- Test: `tests/test_u_des_not_native_alternative.py`

- [ ] Define frozen scalar/tuple-only candidate, reachability, and payload dataclasses.
- [ ] Snapshot CPU/CUDA-like inputs through explicit detached host copies without retaining mutable tensor/array/list/dict references.
- [ ] Canonically hash only semantic fields: state, `dt`, selected control/provenance, map authority ID, commit ID, and schema version.
- [ ] Lock `u_des` to `NOMINAL_REFERENCE`, selected `u` to `SELECTED_EXECUTED_CONTROL`, and prohibit counting `u_des` as a native sibling.
- [ ] Test source mutation after enqueue, aliasing, semantic-hash stability, and enqueue/worker equality.

### Task 3: Implement run-start map authority

**Files:**
- Create: `map_authority.py`
- Create: `schemas/map_authority.schema.json`
- Test: `tests/test_map_authority.py`

- [ ] Hash a stable, sorted relative-path manifest once per run.
- [ ] Include logical name, artifact sizes/hashes, representation and robot/margin/rho contract.
- [ ] Return only a stable `map_authority_id` to each step payload.
- [ ] Fail map freezing as instrumentation health, never L2 UNKNOWN, without changing controller output.
- [ ] Assert full-map hash call count is exactly one per run and zero per step.

### Task 4: Implement nonblocking one-way transport and append-only worker

**Files:**
- Create: `observer_health.py`
- Create: `nonblocking_transport.py`
- Create: `append_only_logger.py`
- Create: `frozen_certifier_adapter.py`
- Create: `shadow_worker.py`
- Create: `lifecycle.py`
- Create: `schemas/step_payload.schema.json`
- Create: `schemas/shadow_result.schema.json`
- Create: `schemas/health_event.schema.json`
- Test: `tests/test_transport_and_worker.py`
- Test: `tests/test_append_only_logs.py`

- [ ] Implement bounded `put_nowait` receipts containing enqueue health only.
- [ ] Expose no result queue, callback, future, response socket, shared result dict, or controller query API.
- [ ] Run frozen read-only adapter calls on worker-owned immutable payloads and label L0/L1 as shadow recomputation.
- [ ] Append capture, result, and health JSONL with stable join keys.
- [ ] Implement bounded end-of-run flush whose timeout records `SHUTDOWN_INCOMPLETE` without changing the trial result.

### Task 5: Implement protected wrapper/decorator fallback

**Files:**
- Create: `instrumented_cbf_wrapper.py`
- Create: `run_with_shadow_instrumentation.py`
- Create: `APPROVED_INSTRUMENTATION_DELTA.md`
- Create: `IMPLEMENTATION_CONTRACT.md`
- Test: `tests/test_wrapper_commit_seam.py`

- [ ] Decorate an existing CBF instance; do not copy/rewrite `run.py`, `solve_QP`, plant dynamics, gates, or candidate selection.
- [ ] Call the frozen `solve_QP`, inspect its completed `solver_success`, capture only successful selected output, and return the exact original object/value.
- [ ] Track deterministic wrapper-side run/trial/step/commit IDs without adding controller gates.
- [ ] Initialize/finalize lifecycle outside the protected script using `runpy` monkeypatching of the imported `CBF` factory.
- [ ] Keep `u_des` nominal-only and native sibling set empty unless supplied by a pre-observation frozen mechanism.

### Task 6: Implement F1-F10 task-local fault QA and future dry-run tooling

**Files:**
- Create: `mock_zero_authority_harness.py`
- Create: `future_equivalence_runner.py`
- Create: `future_equivalence_comparator.py`
- Create: `schemas/future_equivalence_manifest.schema.json`
- Test: `tests/test_fault_injection.py`
- Test: `tests/test_future_equivalence_dry_run.py`
- Create: `audit/mock_zero_authority_fault_injection.json`

- [ ] Exercise worker unavailable, worker crash, queue full, serialization error, map freeze failure, corruption attempt, post-enqueue source mutation, slow worker, certifier exception, and shutdown timeout.
- [ ] Require the deterministic mock controller selected control and return trace to equal observer-disabled trace in all ten cases.
- [ ] Prepare schema/dry-run-only future OFF-vs-ON manifest/comparator; never execute Stonehenge or navigation.

### Task 7: Static audits, reviewers, report, and validation

**Files:**
- Create: `audit/u_des_candidate_role_audit.json`
- Create: `audit/payload_immutability_audit.json`
- Create: `audit/payload_hash_audit.json`
- Create: `audit/map_authority_audit.json`
- Create: `audit/l0_l1_l2_side_effect_audit.json`
- Create: `audit/zero_feedback_static_audit.json`
- Create: `audit/no_collection_audit.json`
- Create: `reviewers/control_theory_review.json`
- Create: `reviewers/robotics_systems_review.json`
- Create: `reviewers/software_architecture_review.json`
- Create: `reviewers/scientific_claim_review.json`
- Create: `FINAL_CASE_DECISION.json`
- Create: `run_manifest.json`
- Create: `downstream_handoff.json`
- Create: `DRAFT_PR_BODY.md`
- Create: `report/REPORT_IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1.md`
- Create: `validate_l2_h1_on_policy_shadow_instrumentation_v1.py`

- [ ] Audit actual frozen L0/L1/L2 source for writes, mutation, caches, RNG, and controller coupling.
- [ ] AST-audit task APIs for forbidden result-return mechanisms and controller forks.
- [ ] Run compileall, unittest, pytest, F1-F10, schema/static validator, `git diff --check`, credential and large-file scans.
- [ ] Re-run PR #96 identity and protected raw-object audit at task end.
- [ ] Require four independent reviewers to select one decision case.
- [ ] Answer all 21 required report questions and freeze the downstream handoff.

### Task 8: Publish only the authorized task-local result

- [ ] Copy only the generated `REPORT*.md` to `C:/Users/zlab/Desktop/REPORT` and mirror compact task evidence to the server maintenance root.
- [ ] Stage only `reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/` because approved production delta is `NONE_REQUIRED`.
- [ ] Commit `feat(reproduction): implement non-invasive L2 H1 shadow instrumentation`.
- [ ] Push `implement-l2-h1-on-policy-shadow-instrumentation-v1` and open one Draft PR against `design-l2-h1-on-policy-shadow-observation-v1`.
- [ ] Stop without executing real equivalence, pilot, cohort, or navigation.
