# Frozen Active Runtime Pilot V3 Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute exactly the ten frozen Pilot V3 trials and preserve complete task-local evidence without changing protocol or shared runtime semantics.

**Architecture:** A thin task-local runner projects the immutable Pilot protocol into the already validated PR #141 Smoke/V3 stack construction path. It delegates all control, certification, routing, commit, token, and trace semantics to frozen runtime objects, while adding Pilot-specific evidence fields and outcome-independent aggregation.

**Tech Stack:** Python 3.10, PyTorch/CUDA 11.8, Git, tmux, JSON/CSV, SHA-256.

---

### Task 1: Seal executable identities before GPU

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/run_active_runtime_pilot_v3.py`
- Create: `reproduction/pilot/active_runtime_pilot_v3/validate_active_runtime_pilot_v3_execution.py`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_EXECUTION_LOCK.json`

- [ ] Compile the task-local Python sources.
- [ ] Run the frozen PR #142 protocol validator in its clean worktree and require all five execution counters to remain zero.
- [ ] Lock the runner, protocol, cohort, map, environment, GPU, V3 geometry, decision rules, and zero execution counts.
- [ ] Run the execution-lock validator and commit `Seal Active Runtime Pilot V3 execution lock`.

### Task 2: Execute the frozen batch

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/raw/gpu_preflight.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/raw/trial_<id>/trial_summary.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/raw/trial_<id>/runtime_trace.jsonl`
- Create: `reproduction/pilot/active_runtime_pilot_v3/raw/trial_<id>/runtime_trace_lock.json`

- [ ] Transfer the exact execution-lock commit to the isolated server checkout.
- [ ] Verify map hashes and the real V3 object graph without running a cycle.
- [ ] Execute trials `5,15,25,35,45,55,65,75,85,95` serially, one fresh process each, at most 500 completed cycles, stopping on any frozen hard block.
- [ ] Persist and verify each trial before starting the next; never rerun complete immutable evidence.

### Task 3: Aggregate and classify without new oracle work

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_TRIAL_RESULTS.csv`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_EXECUTION_SUMMARY.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_TRACE_AUDIT.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_ROUTING_SUMMARY.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_TIMING_SUMMARY.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_FAILURE_REGISTER.csv`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_STRESS_REGRESSION.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_FINAL_DECISION.json`

- [ ] Aggregate only locked runtime facts; do not run a scientific oracle.
- [ ] Separate integrity, hard-safety routing, diagnostic-only shell observations, and liveness diagnostics.
- [ ] Apply the frozen hard-block and method-level rules without parameter or cohort changes.

### Task 4: Validate, commit, and open the Draft PR

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/report/REPORT_ACTIVE_RUNTIME_PILOT_V3.md`
- Modify: `reproduction/pilot/active_runtime_pilot_v3/DRAFT_PR_BODY.md`
- Modify: `reproduction/pilot/active_runtime_pilot_v3/downstream_handoff.json`

- [ ] Copy back the compact task-local evidence and verify hashes.
- [ ] Run the evidence validator, `git diff --check`, and protected-diff audit.
- [ ] Commit `Execute frozen Active Runtime Pilot V3`, push, and create a Draft PR against `freeze-active-runtime-pilot-v3-protocol-v1`.

### Self-review

- [ ] Confirm no Pilot outcome preceded the execution-lock commit.
- [ ] Confirm no shared runtime, prior evidence, protocol, trial, radius, or parameter changed.
- [ ] Confirm Official100, oracle, Formal, and reference-arm counts remain zero.
