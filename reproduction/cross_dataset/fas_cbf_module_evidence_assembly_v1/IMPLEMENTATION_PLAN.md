# FAS-CBF Module Evidence Assembly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assemble auditable, claim-bounded evidence from existing frozen SAFER/FAS-CBF cases without running a new scientific experiment.

**Architecture:** The task records immutable source identities first, then parses only compact reports and existing summaries into normalized evidence records. Deterministic builders derive all matrices, figures, paper architecture, and the single decision from that frozen ledger; the validator rejects any unsupported claim or execution counter.

**Tech Stack:** Python standard library, CSV/JSON, SHA-256, Git/GitHub CLI, existing SSH proxy wrapper, and Matplotlib only for compact static figures.

---

### Task 1: Freeze lineage and source inventory

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/freeze_pr81_and_evidence_roots.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/discover_evidence_sources.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/input_freeze/pr81_and_source_identity.json`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/source_inventory/source_inventory.json`

- [ ] Verify PR #79–#81 are Open Drafts, preserve their exact heads, and create this branch from `e9bf932143542232400b451e3fa6caa888ae3a85`.
- [ ] Define every accepted source by report path, source commit, map role, and SHA-256; mark an unavailable identity as `UNKNOWN` rather than inferring it.
- [ ] Run `python -B freeze_pr81_and_evidence_roots.py` and `python -B discover_evidence_sources.py`.
- [ ] Assert the frozen ETH3D map, reference, method, and baseline hashes match the PR #81 protocol and that no source has a missing report SHA.

### Task 2: Parse only compact evidence and align metric semantics

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/hash_and_inventory_reports.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/parse_compact_metrics.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/audit_metric_semantics.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/semantic_alignment/metric_semantic_alignment.md`

- [ ] Extract only protocol-specified counts, denominators, outcome definitions, and configuration labels from reports or compact JSON/CSV summaries.
- [ ] Preserve original/post-repair, detection/intervention, shadow/active, development/held-out, and map-clearance/mesh-collision/GSplat-overlap distinctions.
- [ ] Run `python -B parse_compact_metrics.py` and `python -B audit_metric_semantics.py`.
- [ ] Fail validation if a metric lacks its sample unit, denominator, source, or semantic boundary.

### Task 3: Build provenance and compatibility audits

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_evidence_provenance_ledger.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/audit_configuration_compatibility.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/audit_cohort_overlap.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/evidence_ledger/evidence_provenance_ledger.csv`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/evidence_ledger/evidence_provenance_ledger.json`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/config_compatibility/configuration_compatibility_matrix.csv`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/config_compatibility/cohort_overlap_audit.json`

- [ ] Build one row per evidence item with provenance, source SHA, role, comparator, claim boundary, and unresolved fields.
- [ ] Classify comparisons as directly comparable, complementary-not-poolable, configuration-specific, map-specific, overlap-risk, or not-comparable.
- [ ] Run both audit scripts and assert no aggregate subtraction or superiority comparison crosses an incompatible configuration boundary.

### Task 4: Derive module and claim matrices

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_module_evidence_matrix.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_claim_evidence_matrix.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_dataset_role_matrix.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_positive_negative_boundary_registry.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/module_matrices/module_evidence_matrix.csv`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/claim_audit/claim_evidence_matrix.csv`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/claim_audit/DT_EVIDENCE_TAXONOMY.md`

- [ ] Grade M-A through M-H by evidence layer rather than a single overall label.
- [ ] Grade C1 through C12 with permitted wording and explicitly prohibited stronger wording.
- [ ] Register positive results, negative ablations, and structural limits without erasing any negative evidence.
- [ ] Assert C5, C7, C9, and C12 cannot become supported without direct same-configuration active evidence.

### Task 5: Freeze paper experiment architecture and minimal decision

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_paper_experiment_architecture.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/select_minimal_remaining_experiment.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/paper_architecture/paper_experiment_architecture.md`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/minimal_remaining_experiment/minimal_remaining_experiment.json`

- [ ] Build E1–E6 as a paper-ready architecture with one evidence role per section.
- [ ] Run a reviewer-facing claim/evidence check and ban a global Full FAS-CBF superiority claim.
- [ ] Select exactly one final status, decision, and next task from the protocol decision tree.

### Task 6: Render compact evidence and validate the package

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/build_compact_figures.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/validate_evidence_assembly.py`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/report/REPORT_ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1.md`
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/report/validation_result.json`

- [ ] Render exactly the 18 required compact figures from ledger and matrix data only.
- [ ] Run the validator, `python -m compileall`, `git diff --check`, and a read-only GPU/SSH watchdog check.
- [ ] Copy only the generated `REPORT*.md` file to `C:\Users\zlab\Desktop\REPORT`.

### Task 7: Publish the bounded evidence package

**Files:**
- Create: `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/report/DRAFT_PR_BODY.md`

- [ ] Inspect the exact staged list; stage only `reproduction/cross_dataset/fas_cbf_module_evidence_assembly_v1/`.
- [ ] Commit with `docs(reproduction): assemble frozen FAS-CBF module evidence`.
- [ ] Push `fas-cbf-module-evidence-assembly-v1` and create the required Draft PR against `eth3d-fas-cbf-stress-scenario-activation-v1`.
- [ ] Verify the new PR is Open Draft and PR #81 remains unchanged.

## Self-review

- [ ] Every included number has a source, unit, denominator, and result-type boundary.
- [ ] Every configuration comparison is classified before any claim is written.
- [ ] No document claims learned-map deployment safety or Full FAS-CBF superiority.
- [ ] No artifact contains trajectories, map arrays, checkpoints, datasets, environments, source checkouts, credentials, or large logs.
