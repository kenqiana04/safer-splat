# Active Runtime Public Cycle Composition V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design, freeze, and validate a runtime-owned public composition root that orchestrates the PR #107–#115 phases without owning safety policy, while preserving PR #120 evidence and preventing any runtime implementation or execution.

**Architecture:** Treat `ActiveCycleCoordinator` as a future orchestration-only object that consumes typed results, asks `Supervisor.route_transition` for every destination, calls existing phase modules, delegates final selection to `Supervisor.arbitrate`, delegates plant/token/trace mechanics to `ActiveRunner`, and returns immutable cycle results. The design records the current public-path gap, an executable transition lookup contract, lifecycle schemas, implementation manifest, scenarios, invariants, and a fail-closed model checker/validator.

**Tech Stack:** Git/GitHub identity gates, Python 3 standard library, JSON/CSV schemas, static source audit, deterministic finite-state model checking, CPU-only design validation.

---

### Task 1: Freeze exact upstream and diagnose the gap

**Files:**
- Create: `reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json`
- Create: `reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_INTEGRATION_GAP_DIAGNOSIS_V2.md`

- [ ] Verify PR #120 Open Draft identity and preserve its blocked status, CE-001, 43/43 assertions, 0/6 genuine E2E, and zero execution counts.
- [ ] Hash PR #107–#120 contract/evidence inputs and the 17 immutable runtime modules.
- [ ] State the missing `MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION` root cause without editing PR #120 or production runtime.

### Task 2: Freeze the composition contract and lifecycle schemas

**Files:**
- Create: `PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md`, `PUBLIC_CYCLE_API_V2.json`, `SUPERVISOR_ROUTING_AUTHORITY_V2.md`
- Create: `EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json`, `PUBLIC_ACTIVE_CYCLE_PHASES_V2.json`, `ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json`
- Create: `DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md`, `PRIMARY_CYCLE_INTEGRATION_V2.md`, `ALTERNATIVE_CYCLE_INTEGRATION_V2.md`
- Create: `BACKUP_CYCLE_INTEGRATION_V2.md`, `TERMINAL_CYCLE_INTEGRATION_V2.md`, `PUBLIC_CYCLE_TRACE_CONTRACT_V2.md`, `ACTIVE_CYCLE_RESULT_SCHEMA_V2.json`

- [ ] Define `ActiveCycleCoordinator` as orchestration-only and `start_trial`, `run_cycle`, and `finalize_trial` as future public APIs.
- [ ] Require Supervisor-owned routing lookup for every stage and preserve PlantCommit/ActiveRunner mechanics.
- [ ] Freeze canonical order, immutable context/result identities, deadline observation points, typed events, and boundary/no-oracle semantics.

### Task 3: Freeze cross-cycle policies, change surface, and implementation handoff

**Files:**
- Create: `PUBLIC_CYCLE_RUNTIME_CHANGE_MATRIX_V2.csv`, `BYPASS_EVIDENCE_PRESERVATION_V2.md`
- Create: `PUBLIC_CYCLE_EVENT_SCHEMA_V2.json`, `FIRST_AND_SUBSEQUENT_CYCLE_SEMANTICS_V2.md`
- Create: `PUBLIC_CYCLE_GOAL_BOUNDARY_V2.md`, `PUBLIC_CYCLE_EXCEPTION_ROUTING_V2.json`
- Create: `PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json`, `PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json`
- Create: `PUBLIC_CYCLE_IMPLEMENTATION_MANIFEST_V2.csv`, `POST_COMPOSITION_VALIDATION_LADDER_V2.md`

- [ ] Make the future patch surface additive (`active_cycle.py` plus only justified types/routing additions), with runtime/protected diff zero in this task.
- [ ] Specify 28+ scenarios, PCC-01–PCC-30 invariants, no synthetic alternative, no outcome/oracle feedback, and explicit BYPASS revalidation policy.
- [ ] Freeze implementation → conformance revalidation → smoke ordering; prohibit design-to-smoke shortcuts.

### Task 4: Freeze design execution and run static model/validator checks

**Files:**
- Create: `PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json`
- Create: `model_check_public_cycle_composition_v2.py`, `public_cycle_design_model_check.json`, `public_cycle_design_counterexamples.json`
- Create: `validate_active_runtime_public_cycle_composition_design_v2.py`, `validation_result.json`, `active_runtime_public_cycle_composition_review.json`

- [ ] Hash the design lock inputs before the official checker/validator run and record CPU-only/zero execution counters.
- [ ] Check exact-one transition resolution, authority separation, phase ordering, no forbidden fallback/plant path, BYPASS preservation, and implementation manifest completeness.
- [ ] Require zero design counterexamples and emit a PASS design verdict only if all checks pass; this task must not implement or revalidate runtime.

### Task 5: Freeze decision, handoff, report, and PR

**Files:**
- Create: `README.md`, `FINAL_DECISION.json`, `downstream_handoff.json`, `DRAFT_PR_BODY.md`
- Create: `report/REPORT_DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2.md`

- [ ] Confirm PR #120 remains unchanged and production/runtime/protected source diff remains zero.
- [ ] Commit design freeze first, then checker/validator/results/report/handoff in the second commit.
- [ ] Push `design-active-runtime-public-cycle-composition-v2` and create one Open Draft PR; do not implement, revalidate conformance, or smoke.
