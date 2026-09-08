# R2 Active Runtime Exception and Unknown Routing Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close D-EXC-001 and D-ALT-001 with typed, lossless exception/UNKNOWN/provider evidence while preserving R1 routing authority and every forbidden runtime blob.

**Architecture:** Add immutable failure and alternative-ingestion types in `runtime_types.py`; add Supervisor-owned phase-failure/provider-status normalization and meta-routing helpers in `supervisor.py`; make `ActiveCycleCoordinator` feed every normal or exceptional result through one destination loop. Existing 43 frozen transition rows, final arbitration, plant commit, token, terminal, trace, and BYPASS semantics remain unchanged.

**Tech Stack:** Python 3 dataclasses/enums, pytest CPU fixtures, JSON/CSV evidence, Git/GitHub CLI.

---

### Task 1: Freeze the exact R2 inputs

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_EXCEPTION_UNKNOWN_REPAIR_INPUT_LOCK.json`
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_REASON_SCOPE_MAPPING_V2.json`

- [ ] **Step 1: Hash PR #124, PR #125, PR #107, PR #110–#112, PR #121, the three allowed runtime files, and every forbidden blob.**
- [ ] **Step 2: Assert PR #125 remains Open Draft at `303aa01c08e82d1d77a5f5cabf5127344109a996`.**
- [ ] **Step 3: Record exact reason-code mappings and the fail-closed `UNRESOLVED_SCOPE` fallback.**

### Task 2: Write failing typed-evidence tests

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_r2_reason_scope_and_failure_types.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_r2_stage_exception_routing.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_r2_alternative_status_fidelity.py`

- [ ] **Step 1: Assert typed enums and immutable records exist.**

```python
assert ReasonScope.UNRESOLVED_SCOPE.value == "UNRESOLVED_SCOPE"
assert StageFailureKind.STAGE_EXCEPTION.value == "STAGE_EXCEPTION"
assert AlternativeInventoryStatus.SOURCE_INVALID.value != PublicCycleEvent.ALT_EXHAUSTED.value
```

- [ ] **Step 2: Inject exceptions at L1, proposal, C0, L2, L3, provider, terminal, and arbitration; assert Supervisor receives typed evidence and resolved destinations execute.**
- [ ] **Step 3: Assert SOURCE_INVALID, PROVENANCE_MISSING, and unknown provider statuses never map to ALT_EXHAUSTED.**
- [ ] **Step 4: Run the new tests and confirm they fail before implementation.**

Run: `python -m pytest reproduction/runtime/active_runtime_assurance_v2/tests/test_r2_*.py -q`

Expected: FAIL because the R2 types/helpers are not implemented.

### Task 3: Implement the typed failure model

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py`

- [ ] **Step 1: Add exact enums.**

```python
class ReasonScope(str, Enum):
    NONE = "NONE"
    CANDIDATE_LOCAL_COMPUTATION = "CANDIDATE_LOCAL_COMPUTATION"
    GLOBAL_AUTHORITY_OR_EVIDENCE = "GLOBAL_AUTHORITY_OR_EVIDENCE"
    INFRASTRUCTURE_HEALTH = "INFRASTRUCTURE_HEALTH"
    UNRESOLVED_SCOPE = "UNRESOLVED_SCOPE"
```

- [ ] **Step 2: Add `StageFailureKind`, frozen `StageFailureEvidence`, `AlternativeInventoryStatus`, and frozen `AlternativeInventoryEvidence`.**
- [ ] **Step 3: Add evidence fields to `ActiveCycleContext`/`ActiveCycleResult` without changing existing positional semantics.**
- [ ] **Step 4: Run type tests until PASS.**

### Task 4: Put exception/provider routing under Supervisor authority

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/supervisor.py`

- [ ] **Step 1: Implement exact reason-code lookup with no substring classification.**
- [ ] **Step 2: Implement phase-specific `route_stage_failure(...)` by mapping exceptions to existing frozen UNKNOWN/no-candidate events where unique.**
- [ ] **Step 3: Implement `route_alternative_inventory(...)`: ALT_AVAILABLE and lawful absence use frozen rows; invalid/provenance/unexpected statuses use a Supervisor meta route to arbitration with `rule_id=None`, never a fake frozen rule.**
- [ ] **Step 4: Preserve `bypass_decision`, `arbitrate`, and `certify_candidate` AST/body hashes.**
- [ ] **Step 5: Run Supervisor and exact-one tests until PASS.**

### Task 5: Execute resolved exception routes in the central loop

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`

- [ ] **Step 1: Make `_safe_call` return typed `StageFailureEvidence`.**
- [ ] **Step 2: Remove `_reason_scope` substring policy and use Supervisor exact mapping.**
- [ ] **Step 3: Replace every exception short-circuit with `route = Supervisor.route_stage_failure(...)`; block only when `route.status != RESOLVED`; otherwise continue the same destination loop.**
- [ ] **Step 4: Normalize provider output to `AlternativeInventoryEvidence`, preserve all four statuses, and route invalid/provenance/unexpected status through Supervisor meta authority.**
- [ ] **Step 5: Convert arbitration exceptions to typed meta block with no action and no plant commit.**
- [ ] **Step 6: Run the three R2 test modules until PASS.**

### Task 6: Freeze source and commit the runtime repair

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_EXCEPTION_UNKNOWN_SOURCE_FREEZE.json`
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_RUNTIME_DIFF_AUDIT_V2.json`

- [ ] **Step 1: Run the package CPU suite and R1 regressions.**
- [ ] **Step 2: Verify changed runtime files are a subset of `active_cycle.py`, `runtime_types.py`, and `supervisor.py`; verify all forbidden blobs exactly match PR #125.**
- [ ] **Step 3: Stage exact source/test/input files and commit.**

Run: `git commit -m "runtime(reproduction): repair active exception and unknown routing V2"`

### Task 7: Build bounded probes, model check, validation, and report

**Files:**
- Create all required task-local JSON/CSV/report/reviewer/handoff artifacts under `implementation_evidence/exception_unknown_routing_repair_v2/`.

- [ ] **Step 1: Run at least 32 CPU-only adversarial probes and record every result.**
- [ ] **Step 2: Run the actual-runtime model checker and require zero counterexamples.**
- [ ] **Step 3: Run all applicable CPU tests, R1 regression checks, and BYPASS static/synthetic checks.**
- [ ] **Step 4: Run the 47-check R2 validator and require `PASS_R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_V2_VALIDATION`.**
- [ ] **Step 5: Recheck PR #125 identity, frozen 43 rows, forbidden blobs, and zero real-execution counters.**
- [ ] **Step 6: Stage exact evidence paths and commit.**

Run: `git commit -m "validation(reproduction): verify exception and unknown routing repair V2"`

### Task 8: Publish one Draft PR

- [ ] **Step 1: Push `repair-active-runtime-exception-and-unknown-routing-v2`.**
- [ ] **Step 2: Create one Open Draft PR with base `repair-active-runtime-authority-and-routing-boundary-v2`.**
- [ ] **Step 3: Verify remote head, PR base/title/state, clean worktree, and exact final SHAs.**

## Self-review

- Spec coverage: D-EXC-001, D-ALT-001, typed scope, 8-stage exception matrix, fallback reachability, provider status fidelity, R1/BYPASS preservation, source freeze, probes/model/validator/report/PR are each assigned above.
- Placeholder scan: no deferred implementation step or outcome-dependent threshold remains.
- Type consistency: `ReasonScope`, `StageFailureEvidence`, `AlternativeInventoryStatus`, and `AlternativeInventoryEvidence` are the sole new evidence vocabulary; Supervisor remains the sole route/policy owner.
