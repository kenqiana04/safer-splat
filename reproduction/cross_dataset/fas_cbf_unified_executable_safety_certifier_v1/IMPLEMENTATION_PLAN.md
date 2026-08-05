# Unified Executable Safety Certifier V1 Implementation Plan

**Execution status:** Completed. The original unchecked items below are retained as the preregistered plan; the realized evidence and final gate are recorded in `report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md` and `report/validation_result.json`.

> **For agentic workers:** REQUIRED SUB-SKILL: execute this plan inline and preserve the single authorized Git scope. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and audit a deterministic candidate-level certifier that commits a control only when actuator, current-feasibility, continuous-segment, and finite terminal-backup evidence all pass.

**Architecture:** A task-owned immutable data-contract layer feeds a single normative dynamics adapter, read-only barrier/CBF adapters, exact or conservative segment backends, a deterministic braking backup certifier, and a unified fail-closed state machine. Synthetic/property tests establish implementation consistency; only after those gates pass does a bounded plant-free frozen-map smoke exercise the same online interfaces.

**Tech Stack:** Python 3, immutable dataclasses, Enum, NumPy, SciPy cKDTree for the frozen isotropic Replica map adapter, pytest, matplotlib, Git/GitHub CLI, and read-only SSH checks.

---

### Task 1: Freeze PR #83 and protected inputs

**Files:**
- Create: `freeze_pr83_inputs.py`
- Create: `input_freeze/pr83_identity.json`
- Create: `input_freeze/pr83_artifact_manifest.json`
- Create: `input_freeze/protected_source_hashes.json`

- [ ] Verify PR #83 is open, draft, mergeable, based on `fas-cbf-module-evidence-assembly-v1`, and headed by `17805e67b75412dc21b1a5fff4143ea3bc985f7f`.
- [ ] Hash the report, execution-model contract, safety-set contract, certificate schema, state machine, interface contracts, P1-P6 registry, module inventory, evidence traceability, and protected sources.
- [ ] Run `python -B freeze_pr83_inputs.py` and expect `PASS_PR83_INPUT_FREEZE`.

### Task 2: Audit and implement the normative execution model

**Files:**
- Create: `adapters/normative_dynamics_adapter.py`
- Create: `proof_artifacts/execution_model_audit.json`
- Create: `proof_artifacts/normative_execution_model.json`
- Create: `proof_artifacts/source_semantics_trace.csv`
- Create: `proof_artifacts/execution_model_consistency.md`
- Test: `tests/test_normative_transition.py`
- Test: `tests/test_normative_interval_flow.py`

- [ ] Record the source expressions `x + dt * double_integrator_dynamics(x,u)` used by plant, candidate verifier, and backup rollout.
- [ ] Implement `transition(state, control)` as `p+dt*v, v+dt*u` and `interval_state(tau)` as `p+tau*v, v+tau*u`.
- [ ] Test exact transitions and interval endpoints; expect both tests to pass.

### Task 3: Implement immutable typed contracts and actuator admission

**Files:**
- Create: `certifier/result_types.py`
- Create: `certifier/actuator_certificate.py`
- Create: `actuator_contract.json`
- Test: `tests/test_actuator_certificate.py`

- [ ] Define frozen serializable `State`, `Control`, `ActuatorBounds`, `BarrierQueryResult`, `SegmentCertificate`, `TerminalCertificate`, `BackupWitness`, and `ExecutableSafetyResult` records.
- [ ] Define all authorized statuses and omit `CERTIFIED_UNRECOVERABLE`.
- [ ] Reject wrong shape and nonfinite values; make hard bounds inclusive; preserve clipping as a newly identified alternative.
- [ ] Run the actuator tests and expect boundary, rejection, provenance, and deterministic serialization cases to pass.

### Task 4: Implement read-only current-map feasibility adapters

**Files:**
- Create: `adapters/gaussian_barrier_adapter.py`
- Create: `adapters/current_cbf_adapter.py`
- Create: `certifier/current_feasibility_certificate.py`
- Test: `tests/test_unknown_is_not_free.py`
- Test: `tests/test_full_query_postcheck.py`

- [ ] Bind every query to a map snapshot and label the result a Gaussian barrier proxy, not metric clearance.
- [ ] Keep reduced-query provenance but require a full-query post-check for certification.
- [ ] Reject unknown, nonfinite, error, and snapshot mismatch without consulting a reference oracle.

### Task 5: Implement continuous swept-segment certification

**Files:**
- Create: `certifier/segment_backends/base.py`
- Create: `certifier/segment_backends/analytic_primitive.py`
- Create: `certifier/segment_backends/conservative_interval.py`
- Create: `certifier/segment_backends/sampled_diagnostic.py`
- Create: `certifier/segment_certificate.py`
- Create: `proof_artifacts/swept_segment_derivation.md`
- Create: `proof_artifacts/swept_segment_assumptions.json`
- Test: `tests/test_segment_endpoint_safe_interior_unsafe.py`
- Test: `tests/test_segment_exact_tangent.py`
- Test: `tests/test_segment_unknown.py`
- Test: `tests/test_segment_map_snapshot_mismatch.py`

- [ ] Implement exact line-segment minima for spheres and synthetic quadratic ellipsoids.
- [ ] Implement a conservative signed-distance interval backend using the proven 1-Lipschitz bound; subdivide until safe, unsafe by a finite witness, or budget-exhausted.
- [ ] Keep dense sampling diagnostic-only and prohibit fallback to it.
- [ ] Verify interior collision, tangent, unknown, snapshot mismatch, and endpoint-only counterexamples.

### Task 6: Implement terminal set and deterministic braking

**Files:**
- Create: `certifier/terminal_set.py`
- Create: `certifier/terminal_certificate.py`
- Create: `certifier/braking_backup_policy.py`
- Create: `proof_artifacts/terminal_set_contract.md`
- Create: `proof_artifacts/braking_policy_derivation.md`
- Test: `tests/test_terminal_zero_velocity_hold.py`
- Test: `tests/test_terminal_nonzero_velocity_reject.py`
- Test: `tests/test_terminal_unknown_reject.py`
- Test: `tests/test_braking_monotonic_velocity.py`
- Test: `tests/test_braking_finite_stop.py`
- Test: `tests/test_zero_actuator_authority.py`

- [ ] Freeze `BRAKING_TO_REST_TERMINAL_SET_V1` with a numerical zero tolerance derived from float64 precision.
- [ ] Require finite current safety and one full zero-hold segment on the same snapshot.
- [ ] Implement componentwise non-reversing `clip(-v/dt,u_min,u_max)` and derive `H_stop` plus one terminal hold.

### Task 7: Implement backup witness and unified certifier

**Files:**
- Create: `certifier/backup_witness.py`
- Create: `certifier/backup_certifier.py`
- Create: `certifier/candidate_library.py`
- Create: `certifier/executable_safety_certifier.py`
- Test: `tests/test_backup_witness_success.py`
- Test: `tests/test_backup_immediate_segment_failure.py`
- Test: `tests/test_backup_future_segment_failure.py`
- Test: `tests/test_backup_terminal_failure.py`
- Test: `tests/test_backup_snapshot_change.py`
- Test: `tests/test_nominal_certified.py`
- Test: `tests/test_alternative_selected.py`
- Test: `tests/test_braking_terminal_selected.py`
- Test: `tests/test_all_candidates_fail_closed.py`
- Test: `tests/test_solver_failure_not_unrecoverable.py`
- Test: `tests/test_deterministic_candidate_order.py`

- [ ] Certify the immediate candidate segment, roll out deterministic braking from `x_1`, certify every segment, and require a terminal zero-hold certificate.
- [ ] Freeze nominal, existing-filtered, task-local alternatives, and braking order with provenance.
- [ ] Commit only the first fully certified candidate; otherwise emit a typed non-execution result without unrecoverability language.

### Task 8: Implement and exhaustively check the state machine

**Files:**
- Create: `certifier/state_machine.py`
- Test: `tests/test_state_machine_all_terminal_paths.py`
- Test: `tests/test_terminal_returns_next_cycle.py`
- Test: `tests/test_infrastructure_separation.py`

- [ ] Encode every success and failure branch from initial diagnosis through next-cycle diagnosis.
- [ ] Enumerate all typed terminal paths and assert each is terminal and returns to the next cycle without a dead state.
- [ ] Keep scientific non-certification separate from infrastructure failure.

### Task 9: Run deterministic synthetic and randomized validation

**Files:**
- Create: `synthetic_cases/SYN-01.json` through `synthetic_cases/SYN-15.json`
- Create: `tests/test_synthetic_cases.py`
- Create: `tests/test_randomized_properties.py`
- Create: `proof_artifacts/property_test_summary.json`

- [ ] Freeze seed `20260805` and analytic expected statuses/reason codes for all 15 cases.
- [ ] Run 10,000 segment, 2,000 braking-witness, and 1,000 typed fail-closed cases.
- [ ] Compare formal segment decisions against high-resolution diagnostic samples only as an implementation-error oracle.
- [ ] Require `false_safe_count=0`; preserve false rejects and inconclusive cases.

### Task 10: State propositions and proof limits

**Files:**
- Create: `proof_artifacts/S1_segment_proposition.md`
- Create: `proof_artifacts/B1_backup_proposition.md`
- Create: `proof_artifacts/R1_tail_witness_proposition.md`
- Create: `proof_artifacts/F1_fail_closed_proposition.md`
- Create: `proof_artifacts/proof_status_registry.json`

- [ ] State S1, B1, R1, and F1 with assumptions, proof sketch, implementation-consistency evidence, and excluded claims.
- [ ] Mark unresolved deployment, disturbance, delay, tracking, map-truth, global completeness, and recursive-feasibility obligations as unproved.

### Task 11: Run bounded frozen-map compatibility smoke

**Files:**
- Create: `map_smoke/run_replica_smoke.py`
- Create: `map_smoke/replica_smoke_records.json`
- Create: `map_smoke/eth3d_compatibility_records.json`

- [ ] Gate map access on all preceding unit/property tests.
- [ ] Select deterministic states only from frozen Replica route/state registries and execute plant-free single-cycle certification.
- [ ] Keep offline reference evaluation separate and at zero online reads; record structurally absent requested classes rather than synthesizing them.
- [ ] Optionally record ETH3D as not executed; do not search candidates or modify its frozen map SHA.

### Task 12: Build figures, timing evidence, report, and final validation

**Files:**
- Create: `figures/*.png` (20 required figures)
- Create: `report/validation_result.json`
- Create: `report/downstream_handoff.json`
- Create: `report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md`
- Create: `report/DRAFT_PR_BODY.md`
- Create: `validate_certifier.py`

- [ ] Build all figures with the required evidence-status labels.
- [ ] Record mean/p50/p95/max timings by certificate outcome without tuning a runtime threshold.
- [ ] Run `python -B -m compileall -q reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1` and expect exit 0.
- [ ] Run `python -B -m pytest -q reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/tests` and expect all tests to pass.
- [ ] Run `python -B validate_certifier.py` and expect `PASS_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_VALIDATION` or the protocol-defined blocker.
- [ ] Run `git diff --check`, inspect exact scope, and verify protected-source hashes and final GPU/watchdog/SSH state.

### Task 13: Publish the bounded implementation

**Files:**
- Stage only: `reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/`

- [ ] Commit exactly `feat(reproduction): implement unified executable safety certifier v1`.
- [ ] Push `fas-cbf-unified-executable-safety-certifier-v1` without amend, rebase, or force.
- [ ] Create one open Draft PR titled `[Draft] Implement actuator-bounded swept-segment and terminal-backup certification` against `fas-cbf-core-v1-conceptual-closure`.
- [ ] Copy only the final `REPORT*.md` to `C:/Users/zlab/Desktop/REPORT` and stop.
