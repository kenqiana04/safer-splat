# Repair Active Runtime Authority and Routing Boundary V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair only D-AUTH-001 and D-TRANS-001 so the Coordinator forwards facts and Supervisor carries the exact frozen 43-rule metadata, while deferring R2 defects.

**Architecture:** Keep `ActiveCycleCoordinator` as a fact/event orchestrator. Move all deadline, alternative-permission, navigation-eligibility, and repeated-route decisions to `Supervisor`; extend immutable routing types so every normative PR107 field travels from frozen row through `TransitionRule` into `RoutingDecision` without destination-derived inference.

**Tech Stack:** Python dataclasses/enums, CSV/JSON frozen contracts, deterministic CPU unittest/static AST checks, Git worktree with two commits.

---

### Task 1: Freeze upstream and repair scope

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/R1_AUTHORITY_ROUTING_REPAIR_INPUT_LOCK.json`
- Create: `.../R1_AUTHORITY_ROUTING_REPAIR_INVARIANTS_V2.json`
- Test: `.../validate_r1_active_runtime_authority_routing_repair_v2.py`

- [ ] Verify PR #124 exact identity and the R1/R2 allocation before editing.
- [ ] Hash PR107/PR110/PR111/PR121 contracts, PR124 audit artifacts, all allowed/forbidden runtime blobs, and BYPASS identities.
- [ ] Record that only D-AUTH-001 and D-TRANS-001 are in scope and that no real execution is authorized.

### Task 2: Write failing authority and metadata tests

**Files:**
- Create: `reproduction/runtime/active_runtime_assurance_v2/tests/test_r1_authority_routing_boundary.py`
- Create: `.../tests/test_r1_transition_metadata_round_trip.py`
- Create: `.../tests/test_r1_destination_derivation.py`
- Create: `.../tests/test_r1_exact_one_and_repeated_guard.py`

- [ ] Assert the Coordinator source has no policy-derived `alternative_search_allowed`, `navigation_timely`, deadline path branch, or direct repeated-state `RoutingDecision` construction.
- [ ] Assert all normative PR107 fields round-trip through `TransitionRule` and `RoutingDecision` for all 43 rows.
- [ ] Assert zero/multi-match are typed blocks, matching destination metadata is not used to infer six unsafe fields, and Supervisor owns the repeated-state guard.

### Task 3: Implement additive routing metadata carriers

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py`
- Modify: `reproduction/runtime/active_runtime_assurance_v2/supervisor.py`

- [ ] Add immutable fields for every normative row attribute to `TransitionRule` and `RoutingDecision`.
- [ ] Load fields mechanically from PR107 CSV; retain exact-one lookup and typed missing/ambiguous outcomes.
- [ ] Make `Supervisor.route_transition` copy matched row metadata exactly, with no destination-based semantic inference.
- [ ] Add a Supervisor-owned runtime meta guard for repeated state without adding a PR107 rule.

### Task 4: Remove Coordinator policy interpretation

**Files:**
- Modify: `reproduction/runtime/active_runtime_assurance_v2/active_cycle.py`

- [ ] Pass raw deadline/backup/candidate/terminal facts into routing context; remove policy-derived flags and deadline branches.
- [ ] Preserve full certified candidate evidence until `Supervisor.arbitrate`; do not set it to `None` for deadline timing.
- [ ] Ask Supervisor for repeated-route typed block; Coordinator only reports the repeated-state fact.
- [ ] Leave D-EXC-001 and D-ALT-001 behavior unchanged and mark both deferred.

### Task 5: Run targeted CPU tests and probes

**Files:**
- Create: `.../R1_PROBE_MANIFEST_V2.json`
- Create: `.../R1_PROBE_RESULTS_V2.json`
- Create: `.../test_manifest.json`
- Create: `.../test_results.json`

- [ ] Run the PR122 package CPU suite and all R1 tests with bytecode disabled.
- [ ] Execute at least 24 deterministic probes covering deadline states, backup states, exact-one, metadata fixtures, repeated guard, and BYPASS static preservation.
- [ ] Do not run R2 gates, full conformance, smoke, ACTIVE, GPU, oracle, official100, or real BYPASS.

### Task 6: Freeze evidence and validate

**Files:**
- Create: all remaining files under `implementation_evidence/authority_routing_boundary_repair_v2/`, including report, handoff, and Draft PR body.
- Modify: none outside the three authorized runtime files and R1 tests.

- [ ] Record source/diff/BYPASS/deferred-defect audits and exact 43/43 round-trip result.
- [ ] Run model/static validator and require all R1 checks to pass with zero forbidden-source changes.
- [ ] Commit runtime/tests as `runtime(reproduction): repair active authority and transition routing V2`.
- [ ] Commit evidence as `validation(reproduction): verify authority and routing boundary repair V2`.
- [ ] Push branch and create one Draft PR based on the audit branch; only hand off to R2.

### Self-review

- [ ] Confirm D-EXC-001 and D-ALT-001 remain `OPEN_DEFERRED_TO_R2`.
- [ ] Confirm no production source, ActiveRunner, PlantCommit, token, terminal, trace, controller, dynamics, map, or oracle file changed.
- [ ] Confirm R1 PASS never authorizes full conformance or smoke directly.
