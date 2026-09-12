# V3 Hard-Radius Runtime Wiring V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit 0.015 q V3 hard-radius authority and wire it through the existing Active Runtime V2 composition without changing certificate mathematics, routing, plant, trace, or historical evidence.

**Architecture:** Keep the V3 implementation additive and task-local. A frozen policy projects a defensive copy of a V2-compatible config, a scoped factory reuses the existing V2 `build_stack`, and a fail-closed object-graph audit verifies one 0.015 q authority across the map adapter, L1/L2 swept backend, terminal certifier, and backup certifier. A task-local `V3AuthorityRegistry` derives every non-geometry authority from the unchanged V2 registry; shared runtime source remains unchanged.

**Tech Stack:** Python 3, frozen dataclasses, standard-library `copy`, `contextlib`, `inspect`, `ast`, `json`, `unittest`, existing Active Runtime V2 and unified certifier packages.

---

### Task 1: Freeze policy and config projection

**Files:**
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/__init__.py`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/geometry_policy.py`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/stack_config.py`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/V3_RUNTIME_GEOMETRY_POLICY_V1.json`
- Test: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests/test_v3_geometry_policy.py`
- Test: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests/test_v3_stack_projection.py`

- [x] **Step 1: Write failing policy tests**

```python
self.assertEqual(V3_GEOMETRY_POLICY.hard_runtime_radius_q, 0.015)
self.assertEqual(V3_GEOMETRY_POLICY.runtime_margin_q, 0.0)
self.assertEqual(V3_GEOMETRY_POLICY.runtime_effective_radius_q, 0.015)
self.assertEqual(V3_GEOMETRY_POLICY.rho_seg_q, 0.0)
self.assertEqual(V3_GEOMETRY_POLICY.historical_diagnostic_radius_q, 0.025)
self.assertFalse(V3_GEOMETRY_POLICY.historical_diagnostic_runtime_authority)
```

- [x] **Step 2: Run the two tests and confirm import failures**

Run: `python -m unittest discover -s reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests -p "test_v3_geometry_policy.py" -v`

Expected: FAIL because the V3 package does not yet exist.

- [x] **Step 3: Implement frozen policy and defensive projection**

Implement a frozen `V3HardRadiusGeometryPolicy` with `validate()` and a `project_v3_runtime_config(base_config)` function that deep-copies input, sets controller/certification fields to `0.015/0/0.015/0`, and stores `0.025` only under `diagnostics.historical_v2_geometry` with `runtime_authority=false`.

- [x] **Step 4: Run policy/projection tests**

Run: `python -m unittest discover -s reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests -p "test_v3_*.py" -v`

Expected: policy and projection tests PASS.

### Task 2: Add explicit V3 authority injection without changing V2 defaults

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/authority_registry.py`
- Test: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests/test_v3_stack_projection.py`

- [x] **Step 1: Add tests for V2 preservation and V3 explicit injection**

```python
v2 = AuthorityRegistry.frozen("map:test", "dt:test")
self.assertEqual(v2.geometry.certification_effective_radius_m, 0.025)
v3 = make_v3_authority_registry("map:test", "dt:test")
self.assertEqual(v3.geometry.certification_effective_radius_m, 0.015)
v2.verify_all()
v3.verify_all()
```

- [x] **Step 2: Implement task-local geometry support**

Implement a task-local frozen `V3AuthorityRegistry` subclass and `make_v3_authority_registry`. Derive all non-geometry authorities from unchanged `AuthorityRegistry.frozen`, replace only the explicitly constructed V3 geometry, and validate the exact frozen V2 non-geometry values plus the exact V3 geometry values. Keep the shared runtime blob and no-argument V2 construction byte-for-byte unchanged.

- [x] **Step 3: Run V3 tests and the existing authority tests**

Run: `python -m unittest reproduction.runtime.active_runtime_assurance_v2.tests.test_authority_registry -v`

Expected: all V2 authority tests PASS.

### Task 3: Reuse V2 composition and verify the live object graph

**Files:**
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/stack_factory.py`
- Create: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests/test_v3_static_wiring.py`

- [x] **Step 1: Write CPU fake-builder and static-source tests**

The fake builder must call `AuthorityRegistry.frozen`, construct a representative shared map/swept/terminal/backup graph, and expose it to the V3 audit. Static tests must confirm the frozen V2 source passes configured `effective_radius` into `SourceGaussianBarrierAdapter` and `SweptSegmentCertifier`, shares `swept` with terminal and backup, and retains Coordinator/Runner/Supervisor/PlantCommit ownership.

- [x] **Step 2: Implement scoped factory and fail-closed audit**

Implement `build_v3_stack(...)` as `project_v3_runtime_config` → scoped explicit replacement of the V2 registry constructor → supplied existing V2 `build_stack` → restoration of the constructor in `finally` → `validate_v3_stack_geometry`. The audit must inspect registry values, configured arguments, closure/object identities, and reject missing or ambiguous evidence.

- [x] **Step 3: Run all targeted tests**

Run: `python -m unittest discover -s reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests -p "test_*.py" -v`

Expected: all targeted CPU tests PASS and no GPU/map access occurs.

### Task 4: Generate validation evidence and report

**Files:**
- Create: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/validate_v3_hard_radius_runtime_wiring_v1.py`
- Generate: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/V3_RUNTIME_HARD_RADIUS_VALIDATION_V1.json`
- Generate: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/V3_RUNTIME_WIRING_FLOW_V1.json`
- Generate: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/V3_DIAGNOSTIC_AUTHORITY_SEPARATION_V1.json`
- Generate: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/V3_PROTECTED_SOURCE_DIFF_V1.json`
- Generate: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/validation_result.json`
- Create: `reproduction/validation/v3_hard_radius_runtime_wiring_v1/report/REPORT_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1.md`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/report/REPORT_IMPLEMENT_V3_HARD_RADIUS_RUNTIME_WIRING_V1.md`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/downstream_handoff.json`
- Create: `reproduction/runtime/v3_hard_radius_runtime_wiring_v1/DRAFT_PR_BODY.md`

- [x] **Step 1: Implement CPU-only validator**

The validator must verify ancestry, exact policy values, config separation, V2 static composition, V3 stack audit evidence, protected diffs, no certifier-math/history changes, no new SI-distance claims, and zero GPU/rollout artifacts. It must write deterministic JSON and the required final status.

- [x] **Step 2: Run targeted and shared regressions**

Run:

```text
python -m unittest discover -s reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests -p "test_*.py" -v
python -m unittest discover -s reproduction/runtime/active_runtime_assurance_v2/tests -p "test_*.py" -v
python -m pytest reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/tests -q
```

Expected: all suites PASS. Any shared regression blocks completion.

- [x] **Step 3: Run validator and diff gates**

Run:

```text
python reproduction/validation/v3_hard_radius_runtime_wiring_v1/validate_v3_hard_radius_runtime_wiring_v1.py --repo-root .
git diff --check
git diff --name-only 606edd1c254f4ffaec48e0b84d8f5e5f29c039ec -- cbf dynamics splat run.py
git diff --name-only 606edd1c254f4ffaec48e0b84d8f5e5f29c039ec -- reproduction/smoke/active_runtime_smoke_v2 reproduction/pilot/active_runtime_pilot_v2
```

Expected: validator `PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1`; protected diff commands emit nothing.

### Task 5: Commit, push, and open Draft PR

**Files:**
- Stage only the two V3 directories plus the justified additive `authority_registry.py` edit.

- [ ] **Step 1: Inspect exact status and staged list**

Run: `git status --short` and `git diff --cached --name-only`.

Expected: no unrelated paths.

- [ ] **Step 2: Commit**

Run: `git commit -m "Implement V3 hard-radius runtime wiring at 0.015q"`.

Expected: one auditable commit on `v3-hard-radius-runtime-wiring-v1`.

- [ ] **Step 3: Push and create Draft PR**

Run: `git push -u origin v3-hard-radius-runtime-wiring-v1`, then create a Draft PR with base `repair-active-runtime-missing-transition-row-v2` and title `[V3] Implement hard-radius runtime wiring at 0.015q`.

Expected: Open Draft PR; no runtime experiment is started.

## Self-review

- [x] Every scientific constant is frozen at 0.015/0/0.015/0 q; 0.025 q is diagnostic-only.
- [x] No placeholder language remains.
- [x] Function/type names are consistent across policy, projection, factory, tests, validator, and reports.
- [x] Shared runtime source is unchanged and existing V2 default tests remain unchanged and passing.
- [x] No Smoke, Pilot, Formal, Reference, Official100, GPU, oracle, tuning, or threshold selection command appears in execution steps.
