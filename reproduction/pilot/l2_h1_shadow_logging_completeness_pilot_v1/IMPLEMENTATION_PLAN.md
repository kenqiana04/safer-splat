# L2/H1 Shadow Logging Completeness Pilot V1 Implementation Plan

> **For agentic workers:** Execute this plan inline and preserve every fail-closed boundary. Do not dispatch extra trials or modify frozen runtime implementation.

**Goal:** Run exactly five preregistered Stonehenge `WRAPPER_ON` pilot trials and determine whether every independently intended control step has complete, joinable, attributable shadow evidence.

**Architecture:** Reuse the exact PR #98 server runner semantics for a C-only serial pilot, freeze trial positions before execution, and retain raw JSONL only under the server maintenance root. A single streaming aggregator computes denominators, integrity checks, compact summaries, and raw-file hashes; a task-local validator then enforces the decision case and Git boundary.

**Tech Stack:** Python 3.10, frozen SAFER-Splat environment, JSONL/CSV, Git/GitHub CLI, SSH to `zlab-4090` physical GPU 1.

---

### Task 1: Freeze identities and pilot selection

**Files:**
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/pilot_trial_selection.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/audit/upstream_identity.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/audit/protected_no_mutation.json`

- [ ] Verify PR #98 is Open Draft at `b47b0e924804e3e446b1f9c184ee5ea5d268d613`.
- [ ] Read the official100 manifest, stable-sort by integer trial, and freeze positions `[10,30,50,70,90]` before any run.
- [ ] Copy the PR #98 protected identity contract into a task-local audit and verify every raw Git blob, size, and mode against HEAD.

### Task 2: Build the C-only server runner and streaming aggregator

**Files:**
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/run_logging_pilot.py`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/aggregate_logging_pilot.py`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/PILOT_PROTOCOL.md`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/README.md`

- [ ] Reuse the PR #98 `server_run_one.py` in `C` mode without changing controller, instrumentation, queue, schema, map, or thresholds.
- [ ] Enforce exactly five fresh serial runs and `PILOT_QA_ONLY` metadata.
- [ ] Derive `N_intended_steps` independently from the committed-control/plant trace, never from capture JSONL.
- [ ] Stream captures, results, health, and map manifests once; detect gaps, duplicates, orphans, schema/alignment failures, map failures, and instrumentation-health errors.
- [ ] Emit only compact summaries and raw artifact path/size/SHA records for Git.

### Task 3: Add bounded tests before server execution

**Files:**
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/tests/test_logging_pilot_tools.py`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/tests/__init__.py`

- [ ] Test independent denominator counting.
- [ ] Test streaming aggregator fixture output.
- [ ] Test duplicate, sequence-gap, and orphan detection.
- [ ] Test legal `L2_UNKNOWN` is separate from instrumentation errors.
- [ ] Test raw artifact hashes and formal-cohort exclusion labels.
- [ ] Run only the task-local tests and compile checks.

### Task 4: Execute exactly five pilot runs on zlab-4090

**Files produced on server only:**
- `/disk1/zlab/maintenance_records/l2_h1_shadow_logging_completeness_pilot_v1/raw_runs/`
- `/disk1/zlab/maintenance_records/l2_h1_shadow_logging_completeness_pilot_v1/compact/`

- [ ] Verify GPU 1 and task process boundary read-only.
- [ ] Materialize an exact detached checkout at PR #98 head with existing frozen map/data links.
- [ ] Run only selected trial IDs once each with `WRAPPER_ON`, fresh process, serial order.
- [ ] On any invalid run or gate failure, stop without repair, replacement, or extra trial.
- [ ] Run the aggregator once and retain raw JSONL exclusively on the server.

### Task 5: Validate compact evidence and select the case

**Files:**
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/pilot_run_manifest.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/environment_identity.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/pilot_per_trial_summary.csv`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/pilot_overall_summary.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/pilot_anomalies.csv`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/raw_artifact_manifest.csv`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/join_integrity.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/sequence_integrity.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/formal_cohort_exclusion.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/validate_l2_h1_shadow_logging_completeness_pilot_v1.py`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/validation_result.json`

- [ ] Verify six completeness rates equal 1.0 for CASE_A and every error count is zero.
- [ ] Verify exactly five valid C runs, no raw JSONL in Git, no controller/instrumentation mutation, and no intervention/replacement.
- [ ] Select the fail-closed Case directly from frozen gates without changing thresholds.

### Task 6: Review, report, and Git closeout

**Files:**
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/reviewers/logging_reproducibility_review.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/reviewers/statistics_claim_review.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/FINAL_CASE_DECISION.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/downstream_handoff.json`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/DRAFT_PR_BODY.md`
- Create: `reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/report/REPORT_VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1.md`

- [ ] Run two short independent-scope reviews and record only verdict, blockers, and recommended case.
- [ ] Generate an answer-first compact report from summaries, without reopening raw JSONL.
- [ ] Recheck PR #98 identity, `git diff --check`, validator, staged file list, and raw-log exclusion.
- [ ] Stage only the task-local directory, commit, push, and create one Open Draft PR based on PR #98 branch.
- [ ] Stop without executing `FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1`.
