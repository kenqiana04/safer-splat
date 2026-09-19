# Multi-Candidate Canonical L2 Evidence Repair V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan task-by-task with checkpoints. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Confirm the Retry1 canonical L2 evidence collision and implement deterministic candidate-scoped L2 evidence without changing runtime safety policy or scientific semantics.

**Architecture:** Preserve the existing per-cycle flat ledger for legacy primary facts and add an independent deterministic `(namespace, candidate identity)` store for observational evidence. `CanonicalL2Runtime` records every candidate in the scoped store and records legacy flat L2 facts only for `CandidateRole.PRIMARY`. Existing trace facts remain additive and canonical JSON serialization remains authoritative.

**Tech Stack:** Python 3, dataclasses/enums from the frozen runtime, unittest/pytest CPU fixtures, Git worktrees.

---

### Task 1: Freeze diagnosis and reproduce H1

**Files:**
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/DIAGNOSIS.md`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/REPAIR_SPEC.md`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/pre_repair_reproduce_h1.py`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/results_cpu_validation/pre_repair_h1_reproduction.json`

- [ ] Hash the frozen Retry1 inputs and extract only witness cycles 15/202, 45/168, 75/281.
- [ ] Run the CPU fixture against unmodified upstream and require `CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_x_k1_identity`.
- [ ] Document the confirmed instrumentation/cardinality root cause and immutable scientific boundaries.
- [ ] Commit diagnosis only as `Diagnose multi-candidate canonical L2 evidence collision`.

### Task 2: Add scoped ledger and L2 recording

**Files:**
- Modify: `reproduction/runtime/certification_execution_state_identity_repair_v1/evidence.py`
- Modify: `reproduction/runtime/certification_execution_state_identity_repair_v1/repaired_components.py`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/validate_multi_candidate_canonical_l2_evidence_v1.py`

- [ ] Add `record_scoped(trial, cycle, namespace, scope_key, **payload)` with idempotent same-payload writes and hard rejection for conflicting writes.
- [ ] Serialize namespaces, scope keys, and payload fields in sorted deterministic order through `facts()`.
- [ ] Record all L2 candidates under `canonical_l2_candidate_evidence` keyed by candidate identity.
- [ ] Keep legacy flat `canonical_l2_*` and `canonical_selected_candidate_identity` writes restricted to `CandidateRole.PRIMARY`.
- [ ] Add CPU tests for primary compatibility, primary+recovery, primary+six F1, conflict rejection, idempotence, role/source, deterministic trace, and no authority mutation.

### Task 3: Validate regressions and frozen witnesses

**Files:**
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/results_cpu_validation/multi_candidate_l2_validation.json`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/results_cpu_validation/frozen_witness_audit.json`
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/results_cpu_validation/protected_diff_audit.json`

- [ ] Run the task validator and related identity-repair, Active Runtime, and bounded-recovery CPU suites.
- [ ] Re-audit the three frozen witness cycles without querying the GPU map.
- [ ] Confirm forbidden source diffs and Retry1 result-root hashes are unchanged.
- [ ] Run `python -m py_compile`, `git diff --check`, and staged-file audits.

### Task 4: Freeze report and publish branch

**Files:**
- Create: `reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/report/FINAL_REPORT.md`

- [ ] Commit runtime repair, tests, validation artifacts, and report as `Repair multi-candidate canonical L2 evidence namespace`.
- [ ] Push only with the existing origin and verify remote HEAD equals local HEAD.
- [ ] Stop without running GPU, tmux, Smoke retry2, Pilot, Formal85, or scientific analysis.
