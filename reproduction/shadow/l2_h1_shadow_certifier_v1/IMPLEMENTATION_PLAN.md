# L2/H1 Shadow Certifier V1 Implementation Plan

> **For agentic workers:** Execute this plan inline, task by task. Do not dispatch subagents; the current task forbids scope expansion and all edits must remain under this directory.

**Goal:** Implement a deterministic, specification-faithful, shadow-only L2/H1 map-relative certifier that reuses PR #84 frozen segment backends without controller, execution, candidate-selection, or fail-close authority.

**Architecture:** A pure H1 propagation function produces `p_k1` and candidate-dependent `p_k2`. A read-only adapter calls the frozen exact-sphere or conservative signed-distance backend directly and optionally calls the frozen sampled diagnostic without granting it formal authority. A typed immutable result records PASS/FAIL/UNKNOWN plus frozen identities and fixed false authority flags; no production hook is created.

**Tech Stack:** Python 3.11, NumPy, stdlib `dataclasses`/`enum`/`unittest`, frozen PR #84 Python backends, Git raw-object identity checks.

---

## File map

- `shadow_types.py`: immutable inputs, propagation values, tri-state result, reason codes, serialization.
- `shadow_contract.py`: frozen PR #93 formulas, robot/margin constants, authority locks, schema contract.
- `frozen_backend_adapter.py`: import and call frozen PR #84 symbols; semantic status mapping only.
- `l2_h1_shadow_certifier.py`: input validation, H1 propagation, snapshot gate, backend call, result assembly.
- `shadow_cli.py`: task-local fixture invocation only; never a controller entry point.
- `fixtures/synthetic_fixtures.py`: deterministic implementation-test fixtures and signed-distance provider.
- `tests/test_*.py`: required identity, oracle, differential, tri-state, diagnostic, and authority coverage.
- `freeze_inputs.py`: raw Git blob/size/mode audit and frozen symbol/specification serialization.
- `build_evidence.py`: deterministic audits, reviewers, diagrams, report, manifest, and PR body.
- `validate_l2_h1_shadow_certifier_v1.py`: fail-closed validator for scope, source identity, tests, claims, and outputs.

### Task 1: Freeze authoritative inputs

**Files:**
- Create: `freeze_inputs.py`
- Create: `audit/frozen_upstream_identity.json`
- Create: `audit/protected_source_audit.json`
- Create: `audit/frozen_specification_identity.json`
- Create: `audit/frozen_backend_symbol_map.json`
- Create: `audit/robot_margin_contract.json`
- Create: `audit/map_snapshot_contract.json`

- [ ] Read PR #93 `PROTECTED_SOURCE_AUDIT.json`; for every record run `git cat-file blob <blob>`, recompute SHA-256/size, and read mode with `git ls-tree <commit> -- <path>`.
- [ ] Freeze PR #83–#93 Open Draft identities and PR #93 expected head `1df09c56eedb53d46f9347695026086319738a89`.
- [ ] Inspect and record exact module, class, method, signature, Git blob, return status, and authority class for the three frozen backends.
- [ ] Hash the PR #93 specification artifacts that define H1, tri-state, map, continuous segment, and robot/margin semantics.
- [ ] Run `python -B freeze_inputs.py`; expect `PASS_L2_H1_SHADOW_INPUT_FREEZE`.

### Task 2: Write failing contract tests

**Files:**
- Create: `tests/test_identity_contract.py`
- Create: `tests/test_h1_propagation.py`
- Create: `tests/test_control_authority.py`
- Create: `tests/test_shadow_tri_state.py`
- Create: `tests/test_map_snapshot_contract.py`
- Create: `tests/test_robot_margin_contract.py`
- Create: `tests/test_sphere_backend_adapter.py`
- Create: `tests/test_ellipsoid_backend_adapter.py`
- Create: `tests/test_continuous_segment_semantics.py`
- Create: `tests/test_endpoint_fallback_disabled.py`
- Create: `tests/test_dense_sample_diagnostic_only.py`
- Create: `tests/test_backend_differential_consistency.py`
- Create: `tests/test_candidate_sensitivity.py`
- Create: `tests/test_nonfinite_unknown.py`
- Create: `tests/test_determinism.py`
- Create: `tests/test_no_control_authority.py`

- [ ] Express T1–T5 and O1–O10 as deterministic `unittest` cases. Core expectations include:

```python
self.assertEqual(propagate_h1_endpoints(x, u_a, dt).p_k1,
                 propagate_h1_endpoints(x, u_b, dt).p_k1)
np.testing.assert_allclose(p2_a - p2_b, dt**2 * (u_a - u_b))
self.assertEqual(certify(snapshot_mismatch).status, ShadowL2Status.UNKNOWN)
self.assertFalse(result.controller_authority)
```

- [ ] Run `python -B -m unittest discover -s tests -v`; expect import/test failures before implementation.

### Task 3: Implement typed shadow contract and H1 propagation

**Files:**
- Create: `shadow_types.py`
- Create: `shadow_contract.py`
- Create: `l2_h1_shadow_certifier.py`

- [ ] Define `ShadowL2Status(PASS, FAIL, UNKNOWN)`, typed reason codes, immutable map/robot/input/result dataclasses, JSON-safe deterministic serialization, and fixed false authority fields.
- [ ] Implement only the frozen propagation:

```python
p_k1 = p_k + dt * v_k
v_k1 = v_k + dt * u_k
p_k2 = p_k + 2.0 * dt * v_k + dt * dt * u_k
```

- [ ] Validate 3-D float64-compatible finite arrays and positive finite scalar `dt`; return typed UNKNOWN rather than converting contract errors to FAIL.
- [ ] Ensure no API accepts `u_k1`, returns a command, or exposes production integration.

### Task 4: Implement frozen-backend adapter

**Files:**
- Create: `frozen_backend_adapter.py`
- Create: `fixtures/synthetic_fixtures.py`

- [ ] Import the actual frozen `certifier` package from the PR #84 task root without copying its geometry logic.
- [ ] Call `ExactSphereSegmentBackend.certify` or `ConservativeSignedDistanceIntervalBackend.certify` with the candidate-dependent H1 endpoints.
- [ ] Map only `CERTIFIED_SAFE -> PASS` and `CERTIFIED_UNSAFE -> FAIL`; every mismatch, nonfinite, budget, query, unsupported, error, or exception maps to typed UNKNOWN.
- [ ] Call `SampledDiagnosticBackend.diagnose` only for a nested diagnostic field; never use it to change formal status.
- [ ] Force `endpoint_fallback_enabled = false` and return UNKNOWN if no frozen formal backend applies.

### Task 5: Complete oracle and differential tests

**Files:**
- Modify: all `tests/test_*.py`
- Create: `audit/backend_differential_consistency.json`
- Create: `audit/candidate_sensitivity_result.json`
- Create: `audit/shadow_reason_to_frozen_taxonomy_mapping.csv`
- Create: `audit/no_control_authority_audit.json`

- [ ] Compare direct frozen backend certificates and adapter results for exact sphere safe/intersection/tangency/endpoint-trap cases and conservative ellipsoid safe/unsafe/inconclusive cases.
- [ ] Repeat identical semantic inputs and compare serialized outputs with no timestamps or UUIDs.
- [ ] Vary sampled diagnostic resolution while asserting unchanged formal status/reason/value.
- [ ] Run `python -B -m unittest discover -s tests -v`; expect every test PASS.

### Task 6: Build compact evidence and four reviews

**Files:**
- Create: `README.md`
- Create: `shadow_cli.py`
- Create: `build_evidence.py`
- Create: `reviewers/control_theory_review.json`
- Create: `reviewers/robotics_systems_review.json`
- Create: `reviewers/software_verification_review.json`
- Create: `reviewers/scientific_claim_review.json`
- Create: `figures/*.png`
- Create: `run_manifest.json`
- Create: `validation_result.json`
- Create: `FINAL_CASE_DECISION.json`
- Create: `downstream_handoff.json`
- Create: `DRAFT_PR_BODY.md`
- Create: `report/REPORT_IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1.md`

- [ ] Generate only task-local fixture logs and four diagrams marked `SHADOW ONLY`, `NO CONTROLLER AUTHORITY`, `NO FORMAL NAVIGATION EXPERIMENT`, `MAP-RELATIVE`, `H1 ONLY`, and `NOT RECURSIVE FEASIBILITY`.
- [ ] Record four independent scoped reviews; CASE_A requires zero critical blockers in all four.
- [ ] Answer report Q1–Q15 first and make no efficacy, runtime, collision, recursive-feasibility, physical-world, or deployment claim.

### Task 7: Validate scope and publish

**Files:**
- Create: `validate_l2_h1_shadow_certifier_v1.py`

- [ ] Run `python -B -m compileall -q .` and `python -B -m unittest discover -s tests -v`.
- [ ] Run pytest only if already installed; do not install dependencies for this task.
- [ ] Run `git diff --check`, secret/large-binary scan, raw-object re-audit, and confirm all diffs are under this task directory.
- [ ] Recheck GPU 1/process/watchdog/SSH read-only state and mirror only compact evidence to the task-owned server directory.
- [ ] Stage exactly `reproduction/shadow/l2_h1_shadow_certifier_v1/`, commit `feat(reproduction): implement shadow-only L2 H1 certifier`, push, and open one Draft PR against `core-v2-causal-increment-specification-v1`.
- [ ] Stop after `PASS_L2_H1_SHADOW_CERTIFIER_V1_VALIDATION`; do not run frozen replay or connect the controller.

## Self-review

- Every protocol section maps to a task above; no production source is modified.
- No placeholder implementation, H2, L3/L4/L5, controller hook, formal rollout, benchmark, tuning, or runtime metric is planned.
- The adapter calls frozen backend code directly; test oracles never validate a rewritten geometry implementation against itself.
