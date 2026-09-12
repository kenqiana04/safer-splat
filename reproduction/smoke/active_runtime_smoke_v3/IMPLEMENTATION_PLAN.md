# Active Runtime Smoke V3 Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a reproducible Stonehenge V3 ACTIVE Runtime Smoke protocol before outcomes, then execute exactly trials 10, 50, and 90 as separate serial GPU processes and preserve complete runtime evidence.

**Architecture:** Keep all changes task-local under `reproduction/smoke/active_runtime_smoke_v3/`. A compact runner imports PR #140's `build_v3_stack_from_frozen_v2`, verifies the immutable map and execution lock before GPU access, executes one trial per process through the existing `ActiveCycleCoordinator`, and persists each trial before advancing. A CPU-only validator gates the protocol commit, while a deterministic postprocessor reconstructs aggregate evidence from immutable per-trial summaries and traces without rerunning completed GPU work.

**Tech Stack:** Python 3, standard-library JSON/CSV/hash/subprocess/statistics, NumPy, PyTorch/CUDA, existing Active Runtime V2 objects, PR #140 V3 geometry policy/config projection/stack factory, Git, GitHub CLI, SSH.

---

### Task 1: Freeze the protocol and input identities

**Files:**
- Create: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json`
- Create: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_INPUT_LOCK.json`
- Create: `reproduction/smoke/active_runtime_smoke_v3/downstream_handoff.json`
- Test: `reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py`

- [ ] **Step 1: Encode the exact frozen inputs**

Write the fixed trial order `[10, 50, 90]`, per-trial maximum `200`, seed `0`, GPU `1`, environment variables, map hashes, controller/dynamics/deadline identities, `0.015/0/0.015/0 q` runtime geometry, and diagnostic-only `0.025 q` shell. Encode every scientific experiment switch as `false`.

- [ ] **Step 2: Add fail-closed protocol assertions**

```python
assert protocol["trial_ids"] == [10, 50, 90]
assert protocol["serial_execution"] is True
assert protocol["separate_process_per_trial"] is True
assert protocol["v3_geometry"]["runtime_effective_radius_q"] == 0.015
assert protocol["v3_geometry"]["historical_diagnostic_runtime_authority"] is False
```

- [ ] **Step 3: Run the CPU-only validator before any GPU work**

Run: `python reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py --repo-root . --phase protocol`

Expected: `PASS_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_VALIDATION` and zero execution counts.

### Task 2: Implement the thin V3 smoke runner

**Files:**
- Create: `reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py`
- Test: `reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py`

- [ ] **Step 1: Add a no-GPU static runner check**

Verify the runner imports `build_v3_stack_from_frozen_v2`, never defines a replacement radius policy, never imports a scientific oracle, and exposes `--preflight`, `--one`, `--all`, and `--summarize` modes.

- [ ] **Step 2: Implement exact input and map verification**

```python
for artifact in protocol["map_artifacts"]:
    actual = {"size": path.stat().st_size, "sha256": sha256_file(path)}
    if actual != {"size": artifact["size"], "sha256": artifact["sha256"]}:
        raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + artifact["relative_path"])
```

The preflight must build one real V3 stack, inspect its `v3_wiring_audit`, and release it without running a cycle.

- [ ] **Step 3: Implement one-trial execution**

Create the frozen Stonehenge state/goal, call `start_trial`, then call `run_cycle` at most 200 times. Each completed cycle must add exactly one trace record; plant commit deltas must be zero or one; committed receipts must be finite, within `[-0.1, 0.1]`, and preserve selected/executed identity. Legal assurance boundaries terminate normally.

- [ ] **Step 4: Implement serial separate-process orchestration**

For each trial in `(10, 50, 90)`, launch a fresh Python process with the frozen environment, persist its summary and trace, confirm the task-owned GPU process exited, and stop only on a protocol-defined hard failure. Existing complete immutable evidence must be verified and skipped rather than rerun.

- [ ] **Step 5: Implement outcome-blind aggregation**

Read only `raw/trial_{id}/trial_summary.json` plus finalized trace/lock files. Produce the required CSV/JSON/report outputs, distinguish task-local reporter defects from runtime failures, and never invoke `run_cycle` from summary mode.

### Task 3: Seal the protocol in Git before GPU execution

**Files:**
- Create: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_EXECUTION_LOCK.json`
- Create: `reproduction/smoke/active_runtime_smoke_v3/DRAFT_PR_BODY.md`

- [ ] **Step 1: Run syntax and protected-diff gates**

Run:

```text
python -m py_compile reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py
python reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py --repo-root . --phase protocol
git diff --check
git diff --name-only 47bd12f1f8efca059775ab294211ed21f7b39d77 -- cbf dynamics splat run.py reproduction/runtime/active_runtime_assurance_v2 reproduction/smoke/active_runtime_smoke_v2 reproduction/pilot/active_runtime_pilot_v2 reproduction/formal
```

Expected: syntax/validator PASS and the protected diff command emits nothing.

- [ ] **Step 2: Commit the immutable protocol source**

Stage only `reproduction/smoke/active_runtime_smoke_v3/` and commit with message `Freeze Active Runtime Smoke V3 protocol`.

- [ ] **Step 3: Write and commit the execution seal**

Record the preceding protocol commit SHA and protocol SHA256 in `SMOKE_V3_EXECUTION_LOCK.json`, validate the seal, and commit it with message `Seal Active Runtime Smoke V3 execution lock`. No GPU command may run before this commit succeeds.

### Task 4: Execute the three frozen GPU trials

**Files:**
- Generate: `reproduction/smoke/active_runtime_smoke_v3/raw/trial_10/**`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/raw/trial_50/**`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/raw/trial_90/**`

- [ ] **Step 1: Run remote CPU/map/V3-object preflight**

Run the frozen runner with `--preflight` using `/disk1/zlab/conda_envs/safer_splat_official/bin/python`, `CUDA_VISIBLE_DEVICES=1`, and the sealed checkout.

Expected: map hashes PASS, V3 object graph reports `0.015/0/0.015/0 q`, diagnostic `0.025 q` has no runtime authority, and no cycle is executed.

- [ ] **Step 2: Execute trial 10 in a fresh process**

Run `--one 10`, persist raw evidence immediately, and verify exit/finalization/trace/GPU cleanup before continuing.

- [ ] **Step 3: Execute trial 50 in a fresh process**

Run `--one 50` only after trial 10's evidence is complete; do not rerun trial 10 for a reporter-only defect.

- [ ] **Step 4: Execute trial 90 in a fresh process**

Run `--one 90` only after trial 50's evidence is complete; stop on any frozen hard-stop condition.

### Task 5: Validate, report, and open the Draft PR

**Files:**
- Generate: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_TRIAL_RESULTS.csv`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_TRACE_AUDIT.json`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_TIMING_SUMMARY.json`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_FAILURE_REGISTER.csv`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_EXECUTION_SUMMARY.json`
- Generate: `reproduction/smoke/active_runtime_smoke_v3/report/REPORT_ACTIVE_RUNTIME_SMOKE_V3.md`
- Update: `reproduction/smoke/active_runtime_smoke_v3/downstream_handoff.json`
- Update: `reproduction/smoke/active_runtime_smoke_v3/DRAFT_PR_BODY.md`

- [ ] **Step 1: Reconstruct aggregate evidence without GPU work**

Run: `python reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py --summarize --checkout . --output-dir reproduction/smoke/active_runtime_smoke_v3`

Expected: all required aggregate files are derived from the three per-trial evidence directories.

- [ ] **Step 2: Run final validation**

Run: `python reproduction/smoke/active_runtime_smoke_v3/validate_active_runtime_smoke_v3_protocol.py --repo-root . --phase evidence`

Expected: `PASS_ACTIVE_RUNTIME_SMOKE_V3` only when all three finalized traces and hard acceptance checks pass.

- [ ] **Step 3: Commit outcome evidence**

Stage only `reproduction/smoke/active_runtime_smoke_v3/` and commit with message `Record Active Runtime Smoke V3 evidence`.

- [ ] **Step 4: Push and create the Draft PR**

Push `freeze-active-runtime-smoke-v3-protocol-v1`, then create an Open Draft PR against `v3-hard-radius-runtime-wiring-v1` titled `[V3] Freeze and execute Active Runtime Smoke protocol`.

Expected: the PR history visibly preserves protocol freeze/seal commits before the evidence commit.

## Self-review

- [x] The plan changes only the task-local V3 Smoke directory.
- [x] Protocol and execution locks precede every GPU outcome.
- [x] Exactly three fixed trials run serially in separate processes.
- [x] The runner reuses PR #140's V3 stack factory and existing Active Runtime objects.
- [x] No scientific oracle, Pilot, Official100, Formal comparison, efficacy analysis, or parameter selection is included.
- [x] Reporter-only defects are repaired from raw evidence without GPU reruns.
- [x] Final success authorizes only the next Pilot-protocol freeze task.
