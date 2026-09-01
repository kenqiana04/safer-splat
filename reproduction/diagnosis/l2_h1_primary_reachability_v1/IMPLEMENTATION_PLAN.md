# L2/H1 Primary Reachability Diagnosis V1 Implementation Plan

> **For agentic workers:** Execute inline in this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain the frozen 14,122-to-zero primary-support funnel using one streaming read, compact evidence, and a bounded source trace without changing any upstream scientific artifact.

**Architecture:** Freeze allowed compact identities first, then test and implement one streaming gate-funnel aggregator. Use its compact outputs to identify the earliest universal blocking gate before performing a 3–5-function source trace. A separate task-local validator checks algebra, evidence support, and zero upstream mutation.

**Tech Stack:** Python 3.11 standard library, JSON/CSV, Git/GitHub CLI, SSH streaming from the frozen server table.

---

### Task 1: Freeze inputs

**Files:**
- Create: `reproduction/diagnosis/l2_h1_primary_reachability_v1/DIAGNOSIS_INPUT_LOCK.json`

- [ ] Verify PR #102 head and the four frozen scientific identities.
- [ ] Read only compact manifests to freeze canonical path, SHA, row count, trial count, `N_primary`, and L2 selected reach.
- [ ] Recompute the input lock after creation and require byte-identical identities.

### Task 2: Test the funnel contract

**Files:**
- Create: `reproduction/diagnosis/l2_h1_primary_reachability_v1/tests/test_reachability_funnel.py`

- [ ] Add exactly five fixtures: universal G6, universal G7, universal G8, overlapping first-failure accounting, and contradiction rejection.
- [ ] Run the test before implementation and require an import failure.
- [ ] Keep fixtures synthetic; never read formal rows in tests.

### Task 3: Stream once and emit compact evidence

**Files:**
- Create: `reproduction/diagnosis/l2_h1_primary_reachability_v1/diagnose_reachability_funnel.py`
- Generate: `reachability_funnel.json`, `gate_failure_counts.csv`, `l1_status_distribution.csv`, `l2_reachability_distribution.csv`, `diagnostic_field_inventory.json`, `gate_dependency_table.csv`, `DATA_ONLY_DIAGNOSIS.json`

- [ ] Implement the frozen G1–G10 order and independent overlapping counts.
- [ ] Assign each row to exactly one earliest failed gate or primary.
- [ ] Count L1/L2 distributions, result-record existence, typed L2 support, and only compact dependency pairs.
- [ ] Stream the server-only canonical table once; emit no rows and copy no table to Git.
- [ ] Verify `sum(first_failure)+N_primary=14122` and frozen Case C consistency.

### Task 4: Trace only the first blocker

**Files:**
- Create: `minimal_code_path.md`, `root_cause_diagnosis.json`, `reachability_diagnosis_review.json`

- [ ] Use only actual compact field names in `git grep -n` after the data-only diagnosis exists.
- [ ] Bound the trace to the writer, gate, and at most 3–5 related functions.
- [ ] Select exactly one D1–D6 label supported by data and code evidence.
- [ ] Do not create a historical bridge unless prospective data plus code remains insufficient.

### Task 5: Validate and close out

**Files:**
- Create: `validate_reachability_diagnosis_v1.py`, `validation_result.json`, `FINAL_CASE_DECISION.json`, `downstream_handoff.json`, `DRAFT_PR_BODY.md`, `README.md`, `report/REPORT_DIAGNOSE_L2_H1_PRIMARY_REACHABILITY_V1.md`

- [ ] Run the five task-local tests and the validator.
- [ ] Recheck all frozen upstream hashes and require zero scientific-artifact changes.
- [ ] Run `git diff --check`, stage only the diagnosis directory, and commit once.
- [ ] Push `diagnose-l2-h1-primary-reachability-v1` and create one Open Draft PR based on `analyze-l2-h1-prospective-shadow-cohort-v1`.
