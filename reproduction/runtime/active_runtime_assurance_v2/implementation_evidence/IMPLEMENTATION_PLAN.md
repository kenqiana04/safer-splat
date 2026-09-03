# Active Runtime Assurance V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the PR #115 additive, typed Active Runtime Assurance V2 package without modifying protected production or specification sources and without running any real rollout.

**Architecture:** Seventeen focused modules communicate only through immutable typed values. `Supervisor.arbitrate` is the sole selection owner, `PlantCommitAdapter.commit` is the sole state-transition owner, and all other modules are authority-limited adapters. Tests use CPU-only injected fakes; the immutable runtime trace is finalized before any post-hoc oracle boundary.

**Tech Stack:** Python 3 stdlib, frozen NumPy/Torch-free runtime dataclasses, injected callable protocols, `unittest`, CSV/JSON, Git content identities.

---

### Task 1: Freeze inputs and core typed contracts

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/runtime_errors.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/authority_registry.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/deadline_runtime.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_runtime_types.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_authority_registry.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_deadline_runtime.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/ACTIVE_RUNTIME_IMPLEMENTATION_INPUT_LOCK.json`

- [ ] **Step 1: Write failing identity, registry and deadline tests**

```python
def test_identity_changes_on_one_field():
    assert action_identity((0.0, 0.0, 0.0), "PRIMARY_NAVIGATION") != action_identity((0.0, 0.0, 0.0), "CERTIFIED_TERMINAL")

def test_active_requires_deadline_profile():
    with self.assertRaises(DeadlineProfileRequired):
        ActiveRunner(mode=RuntimeMode.ACTIVE_RUNTIME_ON, deadline_profile=None)
```

- [ ] **Step 2: Run focused tests and confirm missing-module failures**

Run: `python -B -m unittest tests.test_runtime_types tests.test_authority_registry tests.test_deadline_runtime -v`

Expected: FAIL until the modules exist.

- [ ] **Step 3: Implement deterministic canonical SHA-256 identities, immutable dataclasses, exact authorities and deadline tracker**

```python
def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

class AuthorityRegistry:
    def verify_all(self) -> None:
        if self.geometry.certification_effective_radius_m != 0.025:
            raise AuthorityMismatch("CERTIFICATION_GEOMETRY_AUTHORITY_V2")
```

- [ ] **Step 4: Run focused tests**

Expected: all identity, registry and deadline tests PASS without GPU/network.

### Task 2: Implement admission and certification adapters

**Files:**
- Create: `start_admission.py`, `diagnostic_r0.py`, `l1_runtime.py`, `primary_proposal_adapter.py`, `c0_admission.py`, `l2_runtime.py`, `l3_runtime.py`
- Create: matching `tests/test_*.py`

- [ ] **Step 1: Write injected-fake tests for PASS/FAIL/UNKNOWN, exact actuator bounds, L1 binding reuse, H1 equations, and prepared-only L3 bundles**

```python
def test_c0_rejects_without_clipping():
    result = C0Admission(registry).evaluate(candidate((0.10000001, 0.0, 0.0)), snapshot)
    self.assertEqual(result.status, CertificateStatus.FAIL)
    self.assertEqual(result.candidate_vector, (0.10000001, 0.0, 0.0))
```

- [ ] **Step 2: Run focused tests and confirm failures**

- [ ] **Step 3: Implement minimal adapters with no production mutation or V1 margin import**

```python
p_k1 = tuple(p + dt * v for p, v in zip(state.position, state.velocity))
p_k2 = tuple(p + 2 * dt * v + dt * dt * u for p, v, u in zip(state.position, state.velocity, candidate.vector))
```

- [ ] **Step 4: Run focused tests and static forbidden-import scan**

- [ ] **Step 5: Commit core modules**

Run: `git commit -m "runtime(reproduction): implement active assurance core V2"`

### Task 3: Implement fallback state, arbitration, plant commit, trace and composition root

**Files:**
- Create: `alternative_provider.py`, `backup_token_store.py`, `terminal_runtime.py`, `supervisor.py`, `plant_commit.py`, `trace_writer.py`, `active_runner.py`
- Create: matching tests and synthetic branch tests

- [ ] **Step 1: Write tests for empty native alternatives, token atomicity, terminal eligibility, priority, no-action boundary, selected/executed equality, trace finality and mode gates**

```python
def test_priority(self):
    self.assertEqual(supervisor.arbitrate(navigation=nav, backup=backup, terminal=terminal).selected.role, ActionRole.PRIMARY_NAVIGATION)

def test_boundary_never_steps_plant(self):
    with self.assertRaises(CommitAuthorityViolation):
        plant.commit(boundary_decision, snapshot, boundary_action)
```

- [ ] **Step 2: Run focused tests and confirm failures**

- [ ] **Step 3: Implement transaction-like token updates, typed terminal preparation, sole arbitration, sole commit, append-only trace and BYPASS/ACTIVE composition**

- [ ] **Step 4: Run all module tests**

- [ ] **Step 5: Commit supervisor and fallback modules**

Run: `git commit -m "runtime(reproduction): implement supervisor commit and fallback V2"`

### Task 4: Freeze implementation and run conformance validation

**Files:**
- Create: `implementation_evidence/RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv`
- Create: `implementation_evidence/ACTIVE_RUNTIME_IMPLEMENTATION_INVARIANTS_V2.json`
- Create: `implementation_evidence/test_manifest.json`
- Create: `implementation_evidence/ACTIVE_RUNTIME_IMPLEMENTATION_EXECUTION_LOCK.json`
- Create: `model_check_active_runtime_implementation_v2.py`
- Create: `validate_active_runtime_assurance_v2.py`
- Create: conformance and AST/static tests

- [ ] **Step 1: Copy the frozen 43-row mapping byte-for-byte into the implementation evidence path and test exact ID/destination/authority/failure equivalence**

- [ ] **Step 2: Add AST scans proving only `plant_commit.py` imports/calls the plant function, only `supervisor.py` arbitrates, and no oracle/V1 authority import exists**

- [ ] **Step 3: Freeze all 17 module blobs, transition map, invariant set, test manifest and validator in the execution lock before the complete suite**

- [ ] **Step 4: Run compile/import, complete unit suite, model checker and validator**

Expected: 43/43 mappings, 0 model counterexamples, all tests PASS, `PASS_ACTIVE_RUNTIME_ASSURANCE_V2_IMPLEMENTATION_VALIDATION`.

### Task 5: Close out evidence and Draft PR

**Files:**
- Create: `implementation_evidence/validation_result.json`
- Create: `implementation_evidence/implementation_review.json`
- Create: `implementation_evidence/FINAL_DECISION.json`
- Create: `implementation_evidence/downstream_handoff.json`
- Create: `implementation_evidence/DRAFT_PR_BODY.md`
- Create: `implementation_evidence/report/REPORT_IMPLEMENT_ACTIVE_RUNTIME_ASSURANCE_V2.md`

- [ ] **Step 1: Generate evidence-bound review and report with zero execution/performance claims**

- [ ] **Step 2: Re-run PR #115 identity, protected diff, compile, tests, transition, model, validator and forbidden-import gates**

- [ ] **Step 3: Commit validation artifacts**

Run: `git commit -m "validation(reproduction): verify active runtime assurance V2"`

- [ ] **Step 4: Push and create one Open Draft PR against `design-active-runtime-assurance-implementation-v2`**

- [ ] **Step 5: Copy only the generated `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT`**

The task stops after this closeout. It must not execute `VERIFY_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2`.
