# Active Runtime Public Cycle Composition V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the PR #121 public Active-cycle composition root without changing frozen controller, plant, token, terminal, trace, BYPASS, or scientific semantics.

**Architecture:** Add immutable public-cycle types, an exact-one PR107 transition resolver owned by `Supervisor`, and an orchestration-only `ActiveCycleCoordinator`. The coordinator executes one Supervisor-routed stage at a time and delegates every resolved decision to the unchanged `ActiveRunner` commit/token/trace boundary.

**Tech Stack:** Python 3.11, frozen dataclasses/enums, standard-library CSV/AST/hash tools, `unittest`, CPU deterministic fixtures.

---

### Task 1: Freeze upstream and pre-edit identities

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/public_cycle_implementation_evidence/PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json`
- Create: `reproduction/runtime/active_runtime_assurance_v2/public_cycle_implementation_evidence/prepare_public_cycle_implementation_evidence.py`

- [ ] **Step 1:** Hash all 22 PR #121 design authorities, the PR #120 blocker, 17 runtime modules, protected unchanged modules, and the AST/body of `Supervisor.bypass_decision` and `Supervisor.arbitrate`.
- [ ] **Step 2:** Verify PR #121 remains Open Draft at `4148e671128444d357ea33f6e5c15d0dd2928411`.
- [ ] **Step 3:** Run the existing 78-test CPU baseline and record `OK`.

### Task 2: Add immutable public-cycle types

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_types.py`

- [ ] **Step 1:** Write tests for frozen phases/events, typed routing context/decision, immutable cycle context, trial start, and runtime-only cycle result.
- [ ] **Step 2:** Add only enums/dataclasses; preserve all existing type bodies.
- [ ] **Step 3:** Run the type tests and existing runtime type tests.

### Task 3: Make PR107 routing executable under Supervisor

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/supervisor.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_supervisor_route_transition.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_transition_exact_one_lookup.py`

- [ ] **Step 1:** Extend `TransitionRule` to retain all frozen guard columns while preserving existing fields.
- [ ] **Step 2:** Add exact-one lookup that evaluates mutually exclusive typed context guards and raises typed missing/ambiguous errors.
- [ ] **Step 3:** Add `Supervisor.route_transition(event, runtime_context)` returning `RoutingDecision` without creating an executable action.
- [ ] **Step 4:** Assert 43/43 rows are resolvable and AST hashes for `bypass_decision`, `arbitrate`, and `certify_candidate` remain unchanged.

### Task 4: Implement the public composition root

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_start_trial.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_normal_primary.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_failure_routes.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_fallbacks.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_session_state.py`

- [ ] **Step 1:** Dependency-inject existing registry/admission/diagnostic/L1/P0/C0/L2/L3/alternative/backup/terminal/deadline/Supervisor/ActiveRunner objects.
- [ ] **Step 2:** Implement `start_trial` as startup -> I0a -> route -> R0 diagnostic -> ready, with non-PASS admission returning typed no-plant block.
- [ ] **Step 3:** Implement one-L1-per-cycle `run_cycle` and immutable evidence accumulation.
- [ ] **Step 4:** Route P0/C0/L2/L3/alternative/backup/terminal events exclusively through `Supervisor.route_transition`.
- [ ] **Step 5:** Resolve with existing `Supervisor.arbitrate` then existing `ActiveRunner.commit_active_decision`; never create selected actions in the coordinator.
- [ ] **Step 6:** Implement `finalize_trial` as the unchanged `ActiveRunner.finalize_trace` call plus session finalization.

### Task 5: Cover frozen scenarios and noninterference

**Files:**
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_c0_fail.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_l2_fail.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_l3_fail.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_unknown_routes.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_no_alternative.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_backup_fallback.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_terminal_fallback.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_boundary.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_deadline.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_token_handoff.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_trace.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_bypass_semantics_preserved.py`
- Test: `reproduction/runtime/active_runtime_assurance_v2/tests/test_existing_runtime_regression.py`

- [ ] **Step 1:** Cover all PC-IMP-01..32 outcomes with CPU fakes and exact call histories.
- [ ] **Step 2:** Verify no hard-coded geometry/actuator constants, dynamics import, oracle edge, synthetic candidate, duplicate token update, or duplicate trace.
- [ ] **Step 3:** Run the full runtime suite; expected result is all tests `OK` and no real execution.

### Task 6: Freeze implementation evidence and validate

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/public_cycle_implementation_evidence/EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP_V2.csv`
- Create: `reproduction/runtime/active_runtime_assurance_v2/model_check_public_cycle_implementation_v2.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/validate_active_runtime_public_cycle_composition_v2.py`
- Create: `reproduction/runtime/active_runtime_assurance_v2/public_cycle_implementation_evidence/PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK.json`
- Create: implementation results, review, report, final decision, handoff, and Draft PR body under the evidence directory.

- [ ] **Step 1:** Generate a 43/43 implementation map mechanically from PR107.
- [ ] **Step 2:** Freeze source/test/checker hashes before the final suite.
- [ ] **Step 3:** Run actual-class model checks, PR116 regression, task-local BYPASS regression, and the 40+ check validator.
- [ ] **Step 4:** Commit core, integration, and validation evidence separately; push and open a Draft PR.

### Self-review

- [ ] No protected or PR #107–#121 file is modified.
- [ ] No runtime change falls outside `active_cycle.py`, additive `runtime_types.py`, and additive `supervisor.py`.
- [ ] No placeholder, design rewrite, scientific field, or real execution is introduced.
- [ ] The only downstream task is selected mechanically from the BYPASS gate.
