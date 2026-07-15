# Experiment Protocol Freeze V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the source-backed protocol, configurations, trial cohorts, provenance and validation rules required before any cross-dataset audit.

**Architecture:** The freeze is a self-contained evidence package. Collection scripts read the repository without changing experiment code; the validator checks provenance, registry consistency, isolation boundaries, and bundle hashes.

**Tech Stack:** Python 3 standard library, Git CLI, JSON, CSV, YAML-compatible text, Markdown.

---

### Task 1: Capture immutable provenance

**Files:**
- Create: `reproduction/experiment_protocol_freeze_v1/scripts/collect_freeze_provenance.py`
- Create: `reproduction/experiment_protocol_freeze_v1/provenance/commit_reachability.json`
- Create: `reproduction/experiment_protocol_freeze_v1/provenance/source_file_inventory.csv`

- [ ] Read the specified commits with `git cat-file`, `git show`, and `git merge-base`.
- [ ] Record only source paths, hashes and evidence roles; do not copy or edit source evidence.

### Task 2: Freeze protocol and registries

**Files:**
- Create: `reproduction/experiment_protocol_freeze_v1/EXPERIMENT_PROTOCOL_FROZEN_V1.md`
- Create: `reproduction/experiment_protocol_freeze_v1/METRICS_AND_FAILURE_TAXONOMY.md`
- Create: `reproduction/experiment_protocol_freeze_v1/config_registry.yaml`
- Create: `reproduction/experiment_protocol_freeze_v1/dataset_registry.yaml`
- Create: `reproduction/experiment_protocol_freeze_v1/trial_set_registry.yaml`

- [ ] Freeze only values with source locations.
- [ ] Mark absent facts as `unresolved`; do not infer seeds, orders, checkpoints, or parameter values.

### Task 3: Make the package mechanically auditable

**Files:**
- Create: `reproduction/experiment_protocol_freeze_v1/scripts/validate_freeze_bundle.py`
- Create: `reproduction/experiment_protocol_freeze_v1/validation_result.json`
- Create: `reproduction/experiment_protocol_freeze_v1/freeze_bundle_sha256.json`

- [ ] Validate JSON/CSV/YAML-like registries, reachability, path hashes, trial separation, trial-20 order, and allowed-path-only changes.
- [ ] Set `PASS_WITH_UNRESOLVED_NONCRITICAL_FIELDS` only if no source-backed configuration conflict is found.

### Task 4: Finalize the freeze

**Files:**
- Create: `reproduction/experiment_protocol_freeze_v1/REPORT_EXPERIMENT_PROTOCOL_FREEZE_V1.md`

- [ ] Run collection and validation without GPU execution.
- [ ] Verify the diff is confined to this directory, commit, push, open a PR, and copy only the report to `C:\\Users\\zlab\\Desktop\\REPORT`.
