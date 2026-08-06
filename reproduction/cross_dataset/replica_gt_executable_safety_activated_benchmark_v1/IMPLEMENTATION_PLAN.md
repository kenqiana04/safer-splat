# Replica GT Executable-Safety Activated Benchmark V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: execute this plan inline and preserve the single authorized Git scope. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the preregistered paired B0–B3 benchmark only if PR #84 supplies every frozen method input needed for a fair, reproducible comparison.

**Architecture:** A canonical Git-blob freeze and read-only remote asset freeze feed a method-fairness gate. Candidate generation, registry locking, offline reference evaluation, paired decisions, logical-time rollouts, and statistics are reachable only after that gate passes; a failed gate produces a complete no-execution blocker package without manufacturing missing scientific inputs.

**Tech Stack:** Python 3, Git object plumbing, GitHub CLI, read-only SSH, JSON/CSV, AST inspection, pytest-style assertions, Pillow figures, and deterministic SHA-256 manifests.

---

### Task 1: Freeze PR #84 and external identities

**Files:**
- Create: `freeze_pr84_inputs.py`
- Create: `task_config.py`
- Create: `input_freeze/pr84_identity.json`
- Create: `input_freeze/pr84_artifact_manifest.json`
- Create: `input_freeze/protected_source_hashes.json`
- Create: `input_freeze/replica_map_identity.json`
- Create: `input_freeze/reference_mesh_identity.json`

- [ ] Read PR #84 metadata and require Open, Draft, unmerged, mergeable, exact base/head.
- [ ] Read every frozen repository artifact through `git cat-file blob`, not the working tree.
- [ ] Verify the PR #84 report SHA-256 equals `d22943d8302d344b1c588ac0fb07f5b1aa5a29caa55c08af9eca6a29ce6b1cd3`.
- [ ] Read-only hash the Replica GT-FINE arrays, route/state registries, official mesh, and validated mesh-oracle assets on `zlab-4090`.
- [ ] Reject any mismatch before method construction.

### Task 2: Audit the frozen B0–B3 method contract

**Files:**
- Create: `audit_method_fairness.py`
- Create: `methods/method_registry.json`
- Create: `methods/method_difference_matrix.csv`
- Create: `methods/fairness_audit.json`
- Create: `methods/shared_input_hashes.json`

- [ ] Parse `candidate_library.py` and `executable_safety_certifier.py` from the frozen PR #84 Git blobs.
- [ ] Require a concrete alternative-control value set, size, candidate IDs, provenance, and canonical identity before defining B3.
- [ ] Verify whether `alternative_controls` is internally generated or caller supplied.
- [ ] Mark B0–B3 fair only if the only differences are the preregistered gates and a fully frozen B3 library.
- [ ] If the library content/scale is absent, emit `BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH` and do not evaluate a candidate tuple.

### Task 3: Execute only the reachable scientific phase

**Files:**
- Create if fairness passes: `scenario_generation/*.py`, `registry/*`, `reference/*`, `benchmark/*`, `statistics/*`
- Create if fairness blocks: the same exact output paths with explicit `NOT_EXECUTED_BLOCKED_BEFORE_*` state and zero scientific records.

- [ ] Run no candidate search, future reference query, registry lock, formal decision, or rollout until Task 2 passes.
- [ ] If Task 2 passes, execute Phase 1–4 with seed `20260806`, search cap `300000`, one formal attempt, and frozen quotas.
- [ ] If Task 2 blocks, preserve candidate/search/registry/reference/benchmark/statistics counters at zero and record the exact resume prerequisite.

### Task 4: Build audits, figures, report, and validator

**Files:**
- Create: `build_no_execution_artifacts.py`
- Create: `build_figures.py`
- Create: `build_report.py`
- Create: `validate_benchmark.py`
- Create: `audits/*.json`
- Create: `report/*.json`
- Create: `report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`
- Create: `figures/*.png`

- [ ] Keep represented-map, reference, logical-time, and runtime claims separated.
- [ ] Mark all unavailable scientific panels `BLOCKED PRESEARCH — NO SCIENTIFIC RESULT`.
- [ ] Verify zero map training/mutation, tuning, protected-source mutation, online reference access, and formal attempts.
- [ ] Run syntax compilation, task tests, `git diff --check`, GPU/process checks, and watchdog/SSH checks.

### Task 5: Publish the truthful outcome

**Files:**
- Stage only: `reproduction/cross_dataset/replica_gt_executable_safety_activated_benchmark_v1/`

- [ ] Confirm no out-of-scope files changed.
- [ ] Commit exactly `test(reproduction): benchmark activated executable-safety gates on Replica GT`.
- [ ] Push `replica-gt-executable-safety-activated-benchmark-v1`.
- [ ] Create one Open Draft PR against `fas-cbf-unified-executable-safety-certifier-v1`.
- [ ] Copy only the final `REPORT*.md` to `C:\Users\zlab\Desktop\REPORT`.
