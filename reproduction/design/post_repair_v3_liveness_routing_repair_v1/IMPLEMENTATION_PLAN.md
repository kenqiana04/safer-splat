# Bounded Post-Repair V3 Liveness Routing Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-cycle, finite, fully certified local re-entry opportunity without weakening any existing hard-safety or execution authority.

**Architecture:** Supervisor-owned new disjoint route rows may admit a source-registered six-candidate local library only after primary L3 non-PASS, no valid retained backup, OPEN deadline, and current L1 PASS. The existing C0/L2/L3, canonical transition, arbitration, commit, token, terminal, and trace ownership remain intact; failed recovery returns to terminal/boundary.

**Tech Stack:** Python dataclasses/enums, existing runtime package, CPU fixture tests, then separately authorized engineering GPU validation.

---

This file is a **future** implementation handoff, not authorization to execute it in this design task. Exact modules and gates are frozen in `IMPLEMENTATION_MIGRATION_PLAN.md` and `VALIDATION_LADDER.md`.

### Task 1: Freeze source authority before code

**Files:** Future additive source-authority manifest under the new implementation task; do not alter PR #111 in place.

- [ ] Declare `SOURCE_BOUNDED_LOCAL_RECOVERY_V1` separately from `SOURCE_NATIVE_EXISTING`, with six axis-bound candidates from frozen actuator bounds, deterministic order, one pass per exact numerical state/authority context, and no formal-trial-derived parameter.
- [ ] Verify that the new source is registered and that unregistered/synthetic sources remain C0 FAIL. Expected: authority test PASS, unregistered-source test FAIL closed.

### Task 2: Add typed candidate and routing state

**Files:** Future additive `runtime_types.py`, Supervisor transition-table extension, and CPU routing tests.

- [ ] Add provenance/source and `recovery_attempted_for_state` evidence keyed by canonical numeric state, map, geometry, actuator, deadline profile, and library version; do not use cycle-indexed snapshot identity as the fixed-point key.
- [ ] Add disjoint Supervisor-owned rows for recovery admission, next candidate, exhaustion, certificate PASS/FAIL/UNKNOWN, warning/expiry, and terminal/boundary fallback. Expected: exact-one match for every legal fixture and typed BLOCK for missing/ambiguous lookup.

### Task 3: Wire only a bounded local provider

**Files:** Future task-local recovery provider, additive `active_cycle.py` orchestration hook, CPU fixtures.

- [ ] Enumerate six vectors `(u_max_x,0,0)`, `(u_min_x,0,0)`, `(0,u_max_y,0)`, `(0,u_min_y,0)`, `(0,0,u_max_z)`, `(0,0,u_min_z)` in that frozen order; deduplicate exact vectors, exclude zero, and never perturb, interpolate, or search a path.
- [ ] Reuse the current L1 result with fresh attempt binding for each candidate; call C0→L2→L3 only when routed, stop on first fully certified candidate or exhaust the finite set. Expected: no unverified action and at most six attempts per distinct canonical numeric state/authority context.

### Task 4: Preserve post-decision mechanics

**Files:** Existing `active_runner.py`, `plant_commit.py`, backup-token store, terminal runtime, and canonical transition should remain unchanged unless a separately reviewed shared-runtime diff is unavoidable.

- [ ] Route any certified recovery candidate back to Supervisor arbitration as an `ALTERNATIVE_NAVIGATION` with a matching L3 prepared bundle. Expected: existing ActiveRunner commit/token/trace path, sole PlantCommit.
- [ ] Route exhaustion/unknown through the frozen terminal evaluation and assurance-boundary path. Expected: no zero/nominal fallback masquerading as certified action.

### Task 5: Validate before science

**Files:** Future CPU conformance tests and later separately frozen smoke/pilot/scientific protocols.

- [ ] Run C01–C18 and PO1–PO20, shared BYPASS regression if shared semantics changed, then engineering smoke and pilot on preselected development-exposed trials.
- [ ] Only after all engineering gates PASS, freeze a fresh paired-science protocol before any new formal outcome. Expected: no direct design-to-Formal85 jump.
