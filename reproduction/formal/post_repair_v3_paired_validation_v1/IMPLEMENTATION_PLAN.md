# Post-Repair V3 Paired Validation Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This task is executed inline because the user already authorized end-to-end completion and forbade work outside this task directory.

**Goal:** Freeze a runnable, outcome-blind post-repair Stonehenge paired validation protocol and harness without starting GPU execution.

**Architecture:** The new task directory owns its protocol, authority manifests, runner, analyzer, launcher, validator, CPU fixtures, and execution lock. The runner delegates repaired Active execution to the frozen R6 smoke harness and reads immutable Reference outcomes; the analyzer remains unavailable until all 85 Active trial locks exist and an explicit post-collection flag is provided.

**Tech Stack:** Python 3.10, JSON/CSV, Bash, Git, existing frozen SAFER-Splat runtime.

---

### Task 1: Freeze input identities

**Files:** Create `reproduction/formal/post_repair_v3_paired_validation_v1/freeze_authorities.py`, `PILOT_AUTHORITY_MANIFEST.json`, `REFERENCE_AUTHORITY_MANIFEST.json`, `REFERENCE_FROZEN_OUTCOMES.json`.

- [ ] Read the frozen pilot summary and assert `status == "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1"`, 10 trials, and 5000 cycles/commits/trace records.
- [ ] Inventory every existing Pilot and Formal V2 Reference file as `{path,size,sha256}`, sorted by relative path; compute `sha256(json.dumps(files,sort_keys=True,separators=(",",":")))`.
- [ ] Verify all 85 immutable Reference records in `V3_REFERENCE_REUSE_LOCK.json` and project the 85 archived `reference_hard` values from `V3_PAIRED_PER_PAIR_ANALYSIS.json`, requiring zero hard violations and zero unknowns.
- [ ] Verify the new result root is absent; write only task-local manifests. Run the freezer once and commit its output with the protocol.

### Task 2: Freeze protocol and runnable Active harness

**Files:** Create `POST_REPAIR_V3_PAIRED_PROTOCOL.json`, `run_post_repair_v3_paired_validation_v1.py`, `launch_post_repair_v3_paired_validation_v1.sh`, `monitor_post_repair_v3_paired_validation_v1.py`, `README.md`.

- [ ] Define the exact 85-ID order, seed 0, 500-cycle cap, serial fresh child processes, GPU1, radius 0.015 q, immutable Reference, and future root.
- [ ] Implement `static_preflight()` to validate protocol, manifests, map, protected diff, and missing future root without creating output.
- [ ] Implement `run_one()` by configuring the existing R6 repaired smoke delegate with the new task-local protocol and lock; preserve trace, observation, token, and continuity semantics.
- [ ] Implement `run_batch()` with task-local child authorization, strict subprocess string normalization, no existing-trial rerun, and per-trial immutable evidence locks.
- [ ] Implement launcher ordering: clean source -> CPU validator -> prelaunch-only return OR create root -> GPU preflight -> serial batch. Never invoke launch mode in this freeze task.

### Task 3: Freeze post-collection scientific analysis

**Files:** Create `analyze_post_repair_v3_paired_validation_v1.py`, CPU test fixtures.

- [ ] Refuse execution without explicit `--post-collection-authorized` and 85 complete Active locks.
- [ ] Reuse the frozen V3 1-Lipschitz swept-segment oracle for new Active states at 0.015 q; use archived immutable Reference hard outcomes and exact progress values, with no Reference rerun.
- [ ] Compute paired deltas, 10,000 paired percentile bootstrap resamples with seed 20260911, and strict lower-95%-bound `> -0.02`.
- [ ] Apply integrity-first decision matrix; write the required collection, hard, progress, continuity, routing, witness, failure, and report outputs only after collection.
- [ ] Add CPU synthetic tests for pass/fail/equality/unknown/integrity/near-zero-negative rules; do not query a map or analyze actual outcomes in this task.

### Task 4: Validate, commit, and lock

**Files:** Create `validate_post_repair_v3_paired_validation_v1.py`, `POST_REPAIR_V3_PAIRED_EXECUTION_LOCK.json`.

- [ ] Run CPU fixtures, syntax checks, and `git diff --check`; verify zero protected/runtime diff and no GPU/tmux/Active/Reference/analyzer execution.
- [ ] Commit A: `Freeze post-repair V3 paired scientific validation protocol` with protocol, harness, manifests, tests, and documentation.
- [ ] Hash protocol plus the five final harness files; write a superseding execution lock referencing Commit A.
- [ ] Commit B: `Freeze post-repair V3 paired validation execution lock` containing only the new lock.
- [ ] Re-run `python -m py_compile`, `bash -n`, validator, and launcher `--prelaunch-check-only`; confirm the future root remains absent. Stop before launch.

## Self-review

- [ ] Every required gate and output above is represented by a task-local file or frozen analyzer output.
- [ ] No placeholders, unknown cohort substitutions, Reference rerun path, outcome-conditioned tuning, or runtime-source changes remain.
- [ ] The analyzer is executable only after 85 locked Active outcomes; this freeze task never passes its execution flag.
