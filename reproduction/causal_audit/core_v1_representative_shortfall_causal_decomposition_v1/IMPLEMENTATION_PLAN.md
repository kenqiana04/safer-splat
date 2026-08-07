# Core V1 Representative Shortfall Causal Decomposition V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Causally decompose the frozen Core V1 representative shortfall without modifying any map, formal method, formal cohort, or formal result.

**Architecture:** Freeze PR #84–#89 Git blobs and raw formal evidence first. Reanalyse the frozen 360-state/1440-record formal data, run separately labeled read-only shadow, bounded-oracle, and counterfactual diagnostics only under the pre-registered contracts, then synthesize F01–F11 without treating diagnostic results as formal performance evidence.

**Tech Stack:** Python 3, NumPy/SciPy/Matplotlib, frozen Git blobs, SSH to zlab-4090, task-owned server scripts, JSON/CSV/Markdown, pytest.

---

### Task 1: Freeze source lineage and causal contract

**Files:** `task_config.py`, `freeze_upstream_inputs.py`, `input_freeze/*`, `causes/*`, `phase_manifests/phase0.json`

- [x] **Step 1:** Verify PR #84–#89 identities and write immutable identity JSONs.
- [x] **Step 2:** Read protected Git blobs at frozen commits and record blob ID, byte SHA-256, and size.
- [x] **Step 3:** Create the F01–F11 registry, required-evidence matrix, exact evidence-class separation, GRID7/SOBOL512 and counterfactual contracts before reading diagnostic results.
- [x] **Step 4:** Run the freeze twice and require byte-identical output.

### Task 2: Establish implementation consistency before interpretation

**Files:** `factor_f11_implementation_consistency/*`, `phase_manifests/phase1.json`

- [x] **Step 1:** Verify formal-record identity, shared input quartets, map/frame/unit/bounds fields, candidate order, and logging completeness.
- [x] **Step 2:** Replay 32 frozen states per formal environment twice using task-owned read-only runtime code; compare semantic outputs against E0 records.
- [x] **Step 3:** Independently cross-check Euler, H-stop, braking, terminal membership, sphere-segment, and six-slot serialization formulas.
- [x] **Step 4:** Stop at Case G if any immutable semantic inconsistency is observed.

### Task 3: Reanalyse reachability and statistical limits

**Files:** `factor_f03_b0_masking/*`, `factor_f10_statistical_power/*`, `phase_manifests/phase2.json`

- [x] **Step 1:** Build per-environment B0→B3 conditional funnels from frozen formal records only.
- [x] **Step 2:** Perform independent-gate shadow reporting only for B0-infeasible states and label it E2.
- [x] **Step 3:** Calculate per-environment binomial, cluster, and conditional power without pooling reference tiers.

### Task 4: Audit environment, distribution, and map evidence

**Files:** `factor_f01_environment_exposure/*`, `factor_f07_representative_distribution/*`, `factor_f09_map_representation/*`, `phase_manifests/phase3.json`

- [x] **Step 1:** Derive exposure descriptors from frozen registries and E0 records, preserving physical-versus-represented separation.
- [x] **Step 2:** Inventory available logs and classify missing deployment/on-policy evidence as DATA_BLOCKED.
- [x] **Step 3:** Record map representation/reference tiers and static asset shortfalls without creating a new cohort.

### Task 5: Run bounded diagnostic contracts

**Files:** `factor_f04_b1_timing/*`, `factor_f05_b2_atomicity/*`, `factor_f06_b3_coverage/*`, `factor_f02_configuration_exposure/*`, `phase_manifests/phase4-6.json`

- [x] **Step 1:** Establish the position-first Euler symbolic B1 authority result and compute S0–S3 read-only shadow certificates.
- [x] **Step 2:** Decompose B2 certificates into terminal, braking, zero-hold, and witness components without changing B2.
- [x] **Step 3:** Select C0 by frozen state SHA and C1 by frozen typed failure, then evaluate the pre-registered GRID7/SOBOL512 bounded search with no continuous-space claim.
- [x] **Step 4:** Evaluate the fixed one-factor-at-a-time velocity/dt/acceleration/latency regimes; mark missing nonzero velocity or error budgets DATA_BLOCKED.

### Task 6: Integrate, validate, and publish

**Files:** `causal_attribution/*`, `decision/*`, `report/*`, `figures/*`, `validate_causal_decomposition_audit.py`, `tests/*`

- [x] **Step 1:** Assign one permitted verdict to every factor and evaluate all required interaction terms.
- [x] **Step 2:** Select the fixed Case A–G decision and write claim boundaries and the unique downstream handoff.
- [x] **Step 3:** Generate all 28 required figures with evidence-class and non-claim labels.
- [x] **Step 4:** Run validator, compileall, targeted pytest, Git scope/whitespace/secret/size checks, and final remote GPU/watchdog/SSH audit.
- [x] **Step 5:** Stage only this task directory, commit, push, create one Draft PR, and copy only the final REPORT markdown to Desktop/REPORT.
