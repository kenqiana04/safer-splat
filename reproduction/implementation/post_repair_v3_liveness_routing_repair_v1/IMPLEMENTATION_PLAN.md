# Bounded Local Recovery V1 Implementation Plan

> **For agentic workers:** This is the task-local plan; execute inline in this task because the user requested completion. Keep frozen Gate 0 and protected source read-only.

**Goal:** Add exact Gate 0 F1 recovery as a versioned ACTIVE-only runtime path and validate it with CPU fixtures.

**Architecture:** Provider and trial-local register produce only immutable proposals and search-suppression facts. Supervisor owns typed exact-one routes and final action selection; Coordinator calls existing L1/C0/L2/L3 and ActiveRunner. The ACTIVE commit transaction writes one trace outcome with additive normative recovery evidence.

**Tech Stack:** Python dataclasses/Enum, existing Active Runtime V2 package, pytest, stdlib hashing/struct, Git.

---

### Task 1: Freeze authority and failing tests

**Files:** `reproduction/implementation/post_repair_v3_liveness_routing_repair_v1/{IMPLEMENTATION_PROTOCOL.json,PRE_IMPLEMENTATION_RUNTIME_AUDIT.md,AUTHORIZED_FILE_CHANGESET.json}` and `reproduction/runtime/active_runtime_assurance_v2/tests/test_bounded_local_recovery_v1.py`.

- [ ] Commit the three task-local audit files from exact Gate 0 HEAD.
- [ ] Test generation order, asymmetric endpoints, source admission and key lifecycle; verify red against absent `bounded_recovery.py`.

### Task 2: Implement provider, types and C0 admission

**Files:** `reproduction/runtime/active_runtime_assurance_v2/{bounded_recovery.py,runtime_types.py,c0_admission.py}`.

- [ ] Implement six exact actuator endpoint vectors, float32 bit dedup, fresh candidate provenance, max-six invariant and trial-local cursor.
- [ ] Add typed grant to C0; recovery source without exact grant remains rejected. Run focused CPU tests to green.

### Task 3: Implement Supervisor routing and composition

**Files:** `reproduction/runtime/active_runtime_assurance_v2/{supervisor.py,active_cycle.py}`.

- [ ] Add exact candidate-local L3 FAIL classification and disjoint recovery event/row resolution, preserving historical 44 rows.
- [ ] Add terminal prefetch and scan orchestration using Supervisor-issued next stage. Reuse L1 with fresh binding/C0/L2/L3. Test priority, deadline, unknown, exhaustion, boundary and primary re-entry.

### Task 4: Add ACTIVE-only trace evidence

**Files:** `reproduction/runtime/active_runtime_assurance_v2/{runtime_types.py,commit_transaction.py}`.

- [ ] Attach immutable recovery attempt facts to Supervisor decision and existing one-cycle ACTIVE trace record; no earlier trace append or BYPASS change.
- [ ] Test one outcome per cycle and evidence-incomplete behavior.

### Task 5: Static and regression validation

**Files:** `reproduction/implementation/post_repair_v3_liveness_routing_repair_v1/**`.

- [ ] Run T01–T48, E01–E16, R01–R24, relevant existing CPU suites, exact-one model and protected-source diff.
- [ ] Record BYPASS impact without running real BYPASS; run `py_compile`, validator and `git diff --check`; commit only if full PASS.

No task includes GPU, tmux, map query rollout, scientific analyzer or real PlantCommit.
