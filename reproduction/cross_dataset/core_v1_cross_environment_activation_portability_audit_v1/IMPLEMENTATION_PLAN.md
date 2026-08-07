# Core V1 Cross-Environment Activation Portability Audit V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the preregistered, fail-closed audit of whether frozen Core V1 incremental activation appears in at least two existing non-Replica Gaussian-map environments without changing maps, methods, control parameters, cohorts, references, or gates.

**Architecture:** A task-local Python package freezes upstream Git and server identities, audits the seven preregistered environments, and builds deterministic method-independent registries only where existing assets meet the structural gate. The pipeline stops before B0-B3 whenever fewer than two non-Replica environments can supply at least 80 finite bounds-valid tuples; otherwise it runs one smoke and one formal paired attempt, then emits compact evidence, figures, a validator result, and the fixed Case A-E decision.

**Tech Stack:** Python 3 standard library, NumPy/SciPy/Matplotlib when already available, Git/GitHub CLI, PowerShell, SSH to `zlab-4090`, JSON/CSV/Markdown, pytest and compileall.

---

### Task 1: Freeze lineage and protected identities

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/task_config.py`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/freeze_upstream_inputs.py`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/pr84_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/pr85_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/pr86_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/pr87_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/pr88_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/input_freeze/protected_source_hashes.json`

- [x] **Step 1: Record live PR identities**

Run `gh pr view 84` through `gh pr view 88` with JSON fields for state, draft flag, mergeability, base/head names and OIDs. Expected: all five are open Draft PRs, PR #88 is mergeable, and every frozen head SHA matches the protocol.

- [x] **Step 2: Freeze the normative method/config constants**

Define exactly the four method IDs, `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, `dt=0.05`, acceleration and velocity infinity bounds `0.1`, effective radius `0.11`, terminal tolerance `1e-12`, `H_stop,max=20`, and six-slot SHA `3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe`.

- [x] **Step 3: Hash all protected upstream files**

Read bytes from Git objects at the frozen PR heads, not mutable working-tree substitutes. Expected: the manifest records path, Git commit, size, SHA-256, and role for certifier, method matrix, registry, benchmark, direction decision, map qualification, and environment evidence.

- [x] **Step 4: Run the freeze script twice**

Run `python -B freeze_upstream_inputs.py` twice. Expected: deterministic JSON byte identities and no protected-source mutation.

### Task 2: Audit environment readiness and data quality

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environments/environment_registry.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environments/environment_readiness_matrix.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environments/reference_tier_matrix.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environments/claim_boundary_matrix.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environments/exclusion_log.csv`
- Create: `/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1/audits/environment_asset_inventory.json`

- [x] **Step 1: Inventory only the seven preregistered environments**

Inspect existing server evidence for E1 Replica GT, E2 ETH3D learned 3DGS, E3 TUM SplaTAM, E4 TUM Gaussian-SLAM, E5 Stonehenge, E6 Flight, and E7 TUM Splatfacto negative control. Expected: no E8, no download, no training, no map mutation.

- [x] **Step 2: Evaluate the readiness gates**

For each environment record map identity, scale/frame contract, tuple availability, finite query status, UNKNOWN semantics, clipping status, bounds, reference authority, route provenance, query backend, and adapter compatibility. Expected: every failed item has evidence and a typed `NOT_EVALUABLE` or `ENVIRONMENT_STRUCTURAL_SHORTFALL` reason.

- [x] **Step 3: Validate analytical grain and leakage risk**

Treat one representative tuple as the one-step unit and one natural event episode as the rollout unit. Verify availability before any B0-B3 or future-reference read and report per-environment rates rather than pooled counts across reference tiers.

- [x] **Step 4: Enforce the external-validity stop gate**

Count non-Replica environments able to produce at least 80 method-independent finite bounds-valid tuples with a non-diagnostic backend. Expected: if the count is below two, record Case D and skip Tasks 4-5 scientific execution; do not create data or relax the threshold.

### Task 3: Build and lock representative registries where eligible

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/<env>/sampling_contract.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/<env>/candidate_pool_summary.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/<env>/representative_registry.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/<env>/representative_registry.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/<env>/registry_identity.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/combined_registry_manifest.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/registry/registry_lock_audit.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/audits/selection_leakage_audit.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/audits/prelock_reference_access_log.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/audits/registry_rebuild_audit.json`

- [x] **Step 1: Reuse the frozen Replica registry without resampling**

Verify SHA-256 `eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a` and copy only compact registry evidence into the task directory.

- [x] **Step 2: Construct eligible non-Replica pools using only frozen provenance**

Apply the environment-specific time/arclength/trial fraction rules, exclude out-of-bounds tuples without clipping, stratify by the six frozen fields, and order within strata by canonical tuple SHA-256.

- [x] **Step 3: Rebuild each formal registry in three fresh processes**

Expected: three identical registry SHA-256 values per environment and zero pre-lock method, activation, future-reference, runtime, progress, or collision reads.

- [x] **Step 4: Lock registries immutably**

Expected: no replacement, deletion, reordering, duplication, or activated-sample supplementation after lock. Any contamination emits `BLOCKED_BY_CROSS_ENVIRONMENT_SELECTION_LEAKAGE` and stops.

### Task 4: Implement smoke and formal paired runners

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/methods/method_registry.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/methods/method_difference_matrix.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/methods/shared_contract_hashes.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/methods/fairness_audit.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/run_paired_one_step.py`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/run_natural_event_rollout.py`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/reference/reference_contracts.json`

- [x] **Step 1: Prove B0-B3 contract parity before execution**

Expected: all shared inputs and source hashes match; B3 differs from B2 only through the frozen six-slot alternatives. A mismatch emits `BLOCKED_BY_CROSS_ENVIRONMENT_METHOD_CONTRACT_MISMATCH`.

- [x] **Step 2: Run at most eight fixed states per eligible environment as smoke**

Expected: no tuning, no state replacement, no map mutation, and no formal record contamination.

- [x] **Step 3: Start exactly one formal attempt when the data gate passes**

Run all locked states through B0-B3 on shared inputs and atomically write `one_step_records.csv`. Expected record count is four times the eligible state count, with typed UNKNOWN/nonfinite/infrastructure outcomes retained.

- [x] **Step 4: Run only naturally activated event rollouts**

Use at most 40 events per environment, `max_steps=10`, the frozen plant/controller/map, and no delay or disturbance. Expected: no synthetic activated replacement and no collision-superiority or real-time claim.

### Task 5: Compute references, statistics, and fixed decision gates

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environment_features/environment_feature_contract.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environment_features/state_features.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/environment_features/environment_summary.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/one_step_records.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/natural_event_rollout_records.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/per_environment_summary.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/runtime_summary.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/deadline_audit.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/reference/reference_access_log.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/reference/offline_reference_results.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/statistics/preregistered_hypotheses.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/statistics/per_environment_confidence_intervals.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/statistics/paired_tests.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/statistics/exposure_association.csv`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/statistics/portability_gate_audit.json`

- [x] **Step 1: Compute post-lock environment descriptors**

Leave unavailable metric-reference fields as `NOT_EVALUABLE`; never substitute represented Gaussian clearance for physical reference clearance.

- [x] **Step 2: Compute per-environment paired results**

Calculate Wilson 95% intervals, exact McNemar tests, paired bootstrap estimates, H1-H7 with Holm correction, and separate runtime/deadline summaries. Expected: no pooling across reference tiers.

- [x] **Step 3: Apply the frozen P1-P10 gates**

Qualified environments require `n>=80`, at least five valid incremental activations, positive Wilson lower bound, no leakage, and a consistent method contract. E7 is diagnostic and excluded from every pass/fail count.

- [x] **Step 4: Select exactly one preregistered Case A-E**

If fewer than two non-Replica environments reach the structural gate, choose Case D: `BLOCKED_CORE_V1_PORTABILITY_AUDIT_BY_EXISTING_ASSET_LIMITS` and `UPHOLD_PR88_CASE_D_WITH_EXTERNAL_VALIDITY_UNRESOLVED`.

### Task 6: Generate compact artifacts, figures, and validator

**Files:**
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/decision/causal_interpretation_matrix.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/decision/final_portability_decision.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/decision/claim_boundary.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/decision/downstream_plan.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/report/validation_result.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/report/downstream_handoff.json`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/report/REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/report/DRAFT_PR_BODY.md`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/figures/*.png`
- Create: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/validate_portability_audit.py`

- [x] **Step 1: Generate all required compact outputs**

Create every protocol-required JSON, CSV, Markdown, and all 30 named PNG figures. For skipped scientific execution, figures must visibly state `NOT EVALUATED` or `STRUCTURAL SHORTFALL` rather than fabricate zero-valued observations.

- [x] **Step 2: Write the final report and claim boundary**

The report must preserve the activated Replica mechanism evidence, representative 0/160 evidence, PR #88 Case D, every unavailable environment, unresolved external validity, the 50 ms limitation, and the unique next task.

- [x] **Step 3: Run the validator and tests**

Run `python -B validate_portability_audit.py`, `python -m compileall`, targeted pytest, `git diff --check`, secret/large-file scan, remote GPU/process check, and watchdog/SSH preservation check. Expected validator token: `PASS_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_AUDIT_VALIDATION`.

### Task 7: Publish the bounded audit

**Files:**
- Stage only: `reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/`

- [x] **Step 1: Verify final Git scope**

Run `git status --short` and `git diff --name-only 9287617...`. Expected: every changed path is under the task directory; no maps, datasets, checkpoints, full trajectories, environments, credentials, or large logs are present.

- [ ] **Step 2: Commit and push**

Run `git add reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1`, commit with `test(reproduction): audit Core V1 activation portability across environments`, then push the exact branch without force.

- [ ] **Step 3: Create one Draft PR**

Create the Draft PR against `research-direction-novelty-data-winnability-audit-v1` with the frozen title and generated body. Expected: PR #84-#88 remain unchanged.

- [ ] **Step 4: Copy only the final report**

Copy only `REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md` to `C:\Users\zlab\Desktop\REPORT`; keep all other evidence in Git or the authoritative task root.
