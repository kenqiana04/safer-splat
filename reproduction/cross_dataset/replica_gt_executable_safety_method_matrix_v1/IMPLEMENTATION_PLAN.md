# Replica GT Executable-Safety Method Matrix V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a deterministic, reference-free B0-B3 method contract and six-slot represented-map directional alternative library before any Replica benchmark work.

**Architecture:** The task is self-contained under this directory. It first freezes PR #85/PR #84/raw external identities, then implements a pure float64 directional-library generator with canonical serialization and task-local wrappers. Only synthetic property tests and a generator-only query of the pre-frozen 25-state Replica smoke input are permitted; no certifier decisions, reference-oracle calls, registry construction, or rollout logic is reachable.

**Tech Stack:** Python 3.11, NumPy, pytest, canonical SHA-256/JSON, Git/GitHub CLI, read-only SSH, Pillow for explanatory diagrams.

---

### Task 1: Create the immutable input-freeze evidence

**Files:**
- Create: `task_config.py`, `common.py`, `freeze_pr85_inputs.py`
- Create: `input_freeze/pr85_identity.json`, `input_freeze/pr85_artifact_manifest.json`, `input_freeze/pr84_certifier_identity.json`, `input_freeze/protected_source_hashes.json`, `input_freeze/replica_map_identity.json`, `input_freeze/reference_mesh_identity.json`

- [ ] **Step 1: Implement raw Git-blob identity capture.**

```python
payload = subprocess.run(["git", "cat-file", "blob", oid], check=True, capture_output=True).stdout
record = {"path": path, "git_blob": oid, "sha256": sha256_bytes(payload), "size": len(payload)}
```

- [ ] **Step 2: Verify PR #85, PR #84 and read-only external server hashes before writing the freeze records.**

Run: `python -B reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/freeze_pr85_inputs.py`

Expected: `PASS_PR85_PR84_AND_EXTERNAL_INPUT_FREEZE`.

### Task 2: Reproduce the upstream method gap from canonical PR #84 blobs

**Files:**
- Create: `audits/pr84_candidate_contract_gap.json`, `audits/pr85_fairness_blocker_reproduction.json`, `audits/source_semantics_trace.csv`

- [ ] **Step 1: Parse only canonical bytes for `candidate_library.py` and `executable_safety_certifier.py`.**

```python
assert "alternatives:tuple[Control,...]" in certifier_source
assert "def frozen_candidate_order" in candidate_source
assert "Control(" not in candidate_source
```

- [ ] **Step 2: Fail closed if the reproduced gap differs from PR #85.**

Expected blocker on disagreement: `BLOCKED_BY_UPSTREAM_METHOD_GAP_REPRODUCTION_MISMATCH`.

### Task 3: Implement pure directional geometry and canonical identity

**Files:**
- Create: `alternative_library/result_types.py`, `alternative_library/canonical_serialization.py`, `alternative_library/represented_sphere_frame.py`, `alternative_library/actuator_box_scaling.py`, `alternative_library/deceleration_projection.py`, `alternative_library/directional_library.py`, `alternative_library/contract.py`
- Test: `tests/test_represented_sphere_normal.py`, `tests/test_tangent_frame.py`, `tests/test_axis_fallback.py`, `tests/test_box_scaling.py`, `tests/test_deceleration_projection.py`

- [ ] **Step 1: Write failing geometry/property tests for finite outputs, fixed fallback axes, and actuator-box boundaries.**

```python
result = build_directional_library(state, goal, query, centers, bounds, dt)
assert all(np.max(np.abs(slot.acceleration)) <= 0.1 + 1e-12 for slot in result.available_slots)
```

- [ ] **Step 2: Implement the frozen formulas.**

```python
n = (p - center) / np.linalg.norm(p - center)
t_goal = normalized(goal_unit - float(goal_unit @ n) * n)
u_box = 0.1 * direction / np.max(np.abs(direction))
```

- [ ] **Step 3: Add half-space projection and float64 canonical serialization.**

```python
if float(v @ d_raw) > 0.0:
    d_raw = d_raw - (float(v @ d_raw) / float(v @ v)) * v
```

### Task 4: Freeze B0-B3 nesting and wrappers

**Files:**
- Create: `methods/method_registry.json`, `methods/method_difference_matrix.csv`, `methods/nested_causal_contract.md`, `methods/method_canonical_identity.json`
- Create: `methods/b2_primary_and_braking_wrapper.py`, `methods/b3_directional_library_wrapper.py`
- Test: `tests/test_six_slot_contract.py`, `tests/test_slot_order.py`, `tests/test_deduplication.py`, `tests/test_primary_fairness.py`, `tests/test_b2_b3_only_difference.py`

- [ ] **Step 1: Encode the exact B3 order `PRIMARY`, six slots, `DETERMINISTIC_BRAKING`.**

```python
ORDER = ("PRIMARY-CBF-FILTERED", "ALT-01-OUTWARD", "ALT-02-GOAL-TANGENT", "ALT-03-AUX-TANGENT-POS", "ALT-04-AUX-TANGENT-NEG", "ALT-05-BRAKE-BIASED-GOAL-TANGENT", "ALT-06-BRAKE-BIASED-OUTWARD", "DETERMINISTIC-BRAKING")
```

- [ ] **Step 2: Verify B2 and B3 share primary, bounds, gates and built-in braking; B3 only adds available frozen slots.**

### Task 5: Run deterministic validation without scientific decisions

**Files:**
- Create: `tests/test_unknown_no_reference_fallback.py`, `tests/test_canonical_serialization.py`, `tests/test_process_determinism.py`, `tests/test_candidate_actuator_bounds.py`, `tests/test_no_benchmark_inputs.py`
- Create: `smoke/run_generator_only_replica_smoke.py`, `smoke/generator_only_replica_smoke_records.json`

- [ ] **Step 1: Execute fixed-seed synthetic property suites (20k geometry, 5k axis, 5k projection, 5k serialization).**

Run: `pytest -q reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/tests`

Expected: all pass; no imports of reference/benchmark modules.

- [ ] **Step 2: Run three fresh-process canonical-SHA checks.**

Expected: three equal SHA-256 values and zero mismatches.

- [ ] **Step 3: On the server, query only the frozen represented map for the 25 frozen smoke states and generate records.**

Expected: `GENERATOR_ONLY_REPLICA_SMOKE_PASS`, reference reads 0, formal runs 0.

### Task 6: Build identities, figures, report and validator

**Files:**
- Create: four `alternative_library/*identity*.json` records
- Create: `proof_artifacts/*.md`, `figures/*.png`, `build_figures.py`, `build_report.py`, `validate_method_matrix.py`
- Create: `report/validation_result.json`, `report/downstream_handoff.json`, `report/REPORT_FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1.md`, `report/DRAFT_PR_BODY.md`

- [ ] **Step 1: Hash generator source, config, formulas, map identity and certifier identity into one canonical library identity.**

```python
library_sha256 = sha256_bytes(canonical_json_bytes(identity_payload))
```

- [ ] **Step 2: Produce explanatory-only figures labelled `METHOD DESIGN ONLY`, `NO REFERENCE INPUT`, and `NO SCIENTIFIC OUTCOME`.**

- [ ] **Step 3: Validate zero benchmark counters, no forbidden imports, clean GPU, preserved watchdog/SSH, and all artifact consistency.**

Expected: `PASS_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_FREEZE_VALIDATION`.

### Task 7: Publish the compact evidence package

**Files:**
- Modify only: `reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/**`

- [ ] **Step 1: Stage only the task directory and run `git diff --cached --check`.**

```bash
git add reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1
git diff --cached --check
```

- [ ] **Step 2: Commit, push and create the exact Draft PR against PR #85's branch.**

```bash
git commit -m "feat(reproduction): freeze Replica GT executable-safety method matrix v1"
git push -u origin replica-gt-executable-safety-method-matrix-v1
```

### Self-review

- [ ] Every task requirement is represented above: upstream audit, B0-B3 nesting, six fixed slots, canonical identity, tests, generator-only smoke, reporting, and publication.
- [ ] No step permits a certifier outcome, reference-oracle read, candidate-state search, registry, rollout, tuning, or protected-source change.
- [ ] All later names match the types and artifacts defined by the earlier tasks.
