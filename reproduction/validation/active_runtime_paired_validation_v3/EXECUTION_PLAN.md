# Active Runtime V3 Paired Scientific Validation Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze, validate, commit, and publish the outcome-exposed repeated-benchmark paired-validation protocol without running any new Active V3, Reference, oracle, Official100, or Formal outcome.

**Architecture:** The task-local protocol reuses the exact 85-trial Formal V2 primary cohort and immutable Reference-arm evidence while scheduling only future Active Runtime V3 arms. A machine-readable reference-reuse lock proves each reused arm's summary, raw-evidence lock, trajectory/action evidence, termination, eligibility, start, goal, and frozen execution identities. A CPU-only validator enforces all cohort, geometry, safety, noninferiority, evidence, claim-boundary, and protected-diff rules.

**Tech Stack:** Git/GitHub CLI, Python 3.11 standard library, JSON, CSV, SHA-256, read-only SSH inspection.

---

### Task 1: Lock upstream and immutable Reference evidence

**Files:**
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_REFERENCE_REUSE_LOCK.json`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/build_v3_reference_reuse_lock.py`

- [ ] Verify PR #143 is Open Draft at `974b1957f3da55964814650ec5db6e98c84fc12e` and the current branch descends from that exact commit.
- [ ] Read Formal V2 protocol files from exact commit `ea2dfad6ad1e4b4cb4040e48a70084f7dcbfeab8` without importing or modifying them.
- [ ] Query the frozen server result root read-only and require an accepted, complete, evaluation-eligible `REFERENCE_CBF_QP` arm for every exact primary trial.
- [ ] Recompute the recorded summary, raw-lock, trajectory, action, timing, and termination hashes; stop on any mismatch.
- [ ] Record the exact start state, deterministic goal, method/source/map/controller/dynamics identities, typed termination, oracle-input availability, and evidence hashes for all 85 references.

### Task 2: Freeze the paired-validation protocol

**Files:**
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_TRIAL_MANIFEST.csv`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_INPUT_LOCK.json`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_DECISION_RULES.json`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_REQUIRED_EVIDENCE_SCHEMA.json`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_ANALYSIS_PLAN.md`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.sha256`

- [ ] Freeze the exact 85 IDs and the exact Formal V2 execution order with the 15 development-exposed IDs removed.
- [ ] Freeze future execution as Active V3 only, serial, one process per arm, seed 0, maximum 500 cycles, GPU 1, and the exact environment/map/controller/dynamics identities.
- [ ] Freeze hard safety at `0.015 q` and the historical `0.025 q` shell as diagnostic-only with zero authority.
- [ ] Freeze Reference reuse as required, Reference rerun as unauthorized, and 85/85 paired eligibility as mandatory without imputation.
- [ ] Freeze normalized progress, no clipping, NI margin `-0.02`, 10,000 pair-bootstrap resamples, seed `20260911`, and the strict lower-CI pass rule.
- [ ] Freeze the repeated-benchmark/outcome-exposed inference boundary and all forbidden efficacy/generalization claims.

### Task 3: Implement the CPU-only protocol validator

**Files:**
- Create: `reproduction/validation/active_runtime_paired_validation_v3/validate_v3_paired_validation_protocol.py`

- [ ] Validate the exact upstream ancestor, branch, file hashes, Formal V2 identities, PR #143/Pilot evidence, and 85 Reference reuse records.
- [ ] Validate cohort IDs/order, development exclusion, execution settings, map/checkpoint, geometry, oracle, progress NI, safety gates, and claim boundaries.
- [ ] Validate all execution counters are zero and all changed paths remain task-local.
- [ ] Emit `PASS_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION_PROTOCOL_VALIDATION` and the five required zero counters only when every check passes.

### Task 4: Document and review the frozen protocol

**Files:**
- Create: `reproduction/validation/active_runtime_paired_validation_v3/PROTOCOL_REPORT.md`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/DRAFT_PR_BODY.md`
- Create: `reproduction/validation/active_runtime_paired_validation_v3/downstream_handoff.json`

- [ ] State the repeated-benchmark role, the outcome-exposure limitation, and why this is not a pristine confirmatory holdout.
- [ ] State that Pilot V3 is runtime/integrity evidence, not efficacy evidence.
- [ ] Summarize the exact cohort, Reference reuse, hard-safety and NI gates, zero execution counts, and protected-diff result.
- [ ] Authorize only `EXECUTE_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION` after a successful freeze.

### Task 5: Validate, freeze, and publish

**Files:**
- Stage only: `reproduction/validation/active_runtime_paired_validation_v3/`

- [ ] Run Python compilation and the CPU-only validator; expect PASS plus five zero execution counters.
- [ ] Run `git diff --check` and prove no path outside the task directory changed.
- [ ] Commit as `Freeze Active Runtime V3 paired validation protocol`.
- [ ] Push `freeze-active-runtime-v3-paired-validation-protocol-v1`.
- [ ] Create an Open Draft PR titled `[V3] Freeze Active Runtime paired scientific validation protocol` against `execute-active-runtime-pilot-v3-v1`.
- [ ] Recheck PR state, base, head, and exact SHA; do not execute the validation outcome.
