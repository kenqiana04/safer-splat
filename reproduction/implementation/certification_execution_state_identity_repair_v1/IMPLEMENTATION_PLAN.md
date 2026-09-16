# Certification–Execution State Identity Repair V1 Implementation Plan

> **For agentic workers:** Implement inline in this isolated worktree; do not dispatch subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every safety-relevant predicted endpoint use the exact execution-realizable torch.float32 transition while preserving all frozen method and scientific authorities.

**Architecture:** Add one pure `CanonicalExecutionTransition`, additive L1/L2/L3/token/trace components, and a repaired V3 stack factory that rewires the already-built frozen stack before startup. Supervisor, controller, dynamics equations, geometry, commit transaction, and experiment policy remain unchanged.

**Tech Stack:** Python 3, torch, frozen Active Runtime V2/V3 stack, unittest, one read-only archived CUDA replay.

---

### Task 1: Pure canonical arithmetic

**Files:** `reproduction/runtime/certification_execution_state_identity_repair_v1/canonical_transition.py`; test `reproduction/validation/certification_execution_state_identity_repair_v1/tests/test_canonical_transition.py`.

- [ ] Verify 20 deterministic state/action transitions match frozen plant reference binary32 bits.
- [ ] Verify immediate position is action-independent.
- [ ] Verify L2 second position depends on `u_k` but not on `u_(k+1)`.

Run: `python3 -m unittest reproduction.validation.certification_execution_state_identity_repair_v1.tests.test_canonical_transition -v`

### Task 2: Repaired certificate components and guards

**Files:** `repaired_components.py`, `evidence.py`; test `test_repaired_components.py`.

- [ ] Replace L1 endpoint construction with `T_pos_exec` while preserving once-per-cycle cache/binding.
- [ ] Replace L2 closed form with sequential `T_exec`.
- [ ] Propagate canonical dynamics through L3/backup/terminal, bundle and token lineage.
- [ ] Block synthetic identity mismatch before plant commit.

Run: `python3 -m unittest reproduction.validation.certification_execution_state_identity_repair_v1.tests.test_repaired_components -v`

### Task 3: Additive stack integration

**Files:** `stack_factory.py`.

- [ ] Build frozen V3 stack, recover existing dependencies, and install repaired components before startup.
- [ ] Prove one shared canonical transition across plant/L1/L2/L3/token paths.
- [ ] Prove 0.015/0/0 geometry, Supervisor, controller, and dynamics identities are unchanged.

### Task 4: CPU validation and implementation commit

- [ ] Run `python3 -m py_compile` on all new Python files.
- [ ] Run new deterministic unit tests and frozen relevant CPU regressions unchanged.
- [ ] Run `git diff --check` and protected-tree audit.
- [ ] Commit as `Implement certification-execution state identity repair v1`.

### Task 5: One archived CUDA replay

**Files:** `archived_four_case_replay.py`.

- [ ] With physical GPU1 exposed as process `cuda:0`, load the frozen map once.
- [ ] Replay archived trials 22/28/57/59 without controller, coordinator, plant commit, or rollout.
- [ ] Require repaired L2 and next-L1 endpoints to match archived realized endpoints bitwise and same-segment verdicts to agree.

### Task 6: Freeze validation evidence

**Files:** validator, result summaries, evidence lock, report, handoff.

- [ ] Validate ancestry/spec hashes/protected trees/geometry/no epsilon/no result mutation.
- [ ] Hash the fresh result root into `IMPLEMENTATION_VALIDATION_LOCK.json` and `.sha256`.
- [ ] Commit evidence only as `Record certification-execution identity repair validation evidence`.
- [ ] Stop with next task `FREEZE_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_PROTOCOL_V1` only if every gate passes.
