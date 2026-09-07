# BYPASS QA Trace Identity Repair V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair only the task-local BYPASS QA trial-identity plumbing and freeze a fresh, independent V2R1 equivalence execution protocol without running real trial arms.

**Architecture:** One canonical formatter maps each frozen native Stonehenge index to an arm-independent trial identity. The reference/BYPASS adapter, runtime snapshot, trace writer, manifests, trace metadata, and comparator join keys consume that same object; arm identity remains a separate typed field. CPU synthetic tests exercise the real PR #116 BYPASS commit/trace path while immutable PR #117 evidence and runtime contracts remain protected.

**Tech Stack:** Python 3.10, `unittest`, frozen Active Runtime Assurance V2 Python modules, JSON/Markdown, Git/GitHub CLI.

---

### Task 1: Repair task-local identity plumbing

**Files:**
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/canonical_trial_identity.py`
- Modify: `reproduction/validation/active_harness_bypass_equivalence_v2/reference_trial_adapter.py`
- Modify: `reproduction/validation/active_harness_bypass_equivalence_v2/run_qa_pipeline.py`
- Modify: `reproduction/validation/active_harness_bypass_equivalence_v2/compare_bypass_equivalence.py`

- [x] Add one strict `make_canonical_trial_identity(native_trial_index)` formatter using `STONEHENGE_TRIAL_{index:03d}`.
- [x] Feed the same canonical identity to snapshot, writer, arm manifest, trace metadata, and comparison join key.
- [x] Keep `REFERENCE`/`BYPASS` as separate arm metadata and preserve strict `TRIAL_IDENTITY_MISMATCH` behavior.

### Task 2: Prove the repair on CPU

**Files:**
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/tests/test_trace_identity_one_step_bypass.py`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/tests/test_reference_bypass_trial_identity_pairing.py`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/tests/test_trace_identity_negative_cases.py`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/tests/test_reference_source_lock_regression.py`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/tests/test_bypass_plantcommit_regression.py`

- [x] Exercise startup through `ActiveRunner.commit_bypass`, plant commit, trace append, finalize, and immutable-lock enforcement.
- [x] Prove all five native indices pair by canonical trial ID, never by filename or arm-encoded identity.
- [x] Prove mismatched IDs still fail and the PR #117 BYPASS-only PlantCommit correction remains bounded.
- [x] Run the new suite (11/11) and all PR #116 runtime tests (78/78) before the repair commit.

### Task 3: Freeze V2R1 contracts and locks

**Files:** Create the required task-local protocol, identity/schema/invariant contracts, repair locks, future execution-lock templates, source-lock regression evidence, report, review, validator, decision, and handoff files.

- [x] Freeze IDs `[10,30,50,70,90]`, sentinel-first order, fresh pairs, bit-exact equality, hard cap 10, and correction quota 0.
- [x] Bind the repair execution lock to the committed repair source and test identities.
- [x] Mark every real/GPU/ACTIVE/oracle/official100 execution count as zero.

### Task 4: Validate and publish

**Files:**
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/validate_bypass_qa_trace_identity_repair_v2.py`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/validation_result.json`
- Create: `reproduction/validation/bypass_qa_trace_identity_repair_v2/trace_identity_repair_review.json`

- [x] Recheck PR #117 identity, protected diffs, old evidence immutability, tests, lock hashes, and no-execution counters; validator passed 28/28.
- [x] Prepare only the task-local refreeze artifacts for the second commit, branch push, and specified Open Draft PR.
- [x] Copy only the final `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT` and stop before V2R1 execution.
