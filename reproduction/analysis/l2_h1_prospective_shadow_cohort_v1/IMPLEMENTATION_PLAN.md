# L2/H1 Prospective Shadow Cohort Analysis V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: execute this plan task-by-task in the current isolated worktree. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unlock and analyze the frozen 100-trial prospective shadow cohort exactly once under the PR #100 analysis and claim contracts.

**Architecture:** A pre-reveal gate verifies all upstream and data commitments, then synthetic tests freeze a streaming analyzer and its execution lock. The locked analyzer builds a server-only canonical table, writes and hashes the primary result before any secondary computation, and emits only compact results, figures, reviews, validation, and a report to Git.

**Tech Stack:** Python 3.10, standard-library JSON/CSV/hashlib/random/statistics, NumPy for deterministic percentiles, Matplotlib for compact figures, Git/GitHub CLI, SSH to zlab-4090.

---

### Task 1: Verify upstream and create the scientific unlock

**Files:**
- Create: `reproduction/analysis/l2_h1_prospective_shadow_cohort_v1/SCIENTIFIC_ANALYSIS_UNLOCK.json`
- Create: `reproduction/analysis/l2_h1_prospective_shadow_cohort_v1/analysis_input_identity.json`

- [ ] Verify PR #101 is Open Draft at `fbd4f3744e8b6d0448644c00cd8fdb1e8295902d`.
- [ ] Recompute protocol, execution-lock, collection-lock, raw-manifest, result-commitment, and ordered-result commitments without reading any real `l2_status`.
- [ ] Confirm 100 formal trials, formal data role, strict collection QC, namespace separation, and zero post-data deviations.
- [ ] Write an unlock artifact with `outcomes_read_before_unlock=false` and `unlock_authorized=true`.

### Task 2: Implement and test the analyzer before reveal

**Files:**
- Create: `build_formal_analysis_table.py`
- Create: `analyze_primary_endpoint.py`
- Create: `bootstrap_primary_by_trial.py`
- Create: `analyze_secondary_endpoints.py`
- Create: `validate_formal_analysis_v1.py`
- Create: `tests/test_formal_analysis_contracts.py`
- Create: `tests/test_bootstrap_and_locks.py`

- [ ] Write synthetic tests for all 14 frozen test cases, including UNKNOWN denominator inclusion, duplicate rejection, QA rejection, deterministic clustered bootstrap, zero-denominator redraw, and prohibited-claim audit.
- [ ] Run tests before implementation and confirm they fail for missing modules.
- [ ] Implement only the frozen eligibility, tri-state algebra, join integrity, bootstrap, secondary, and lock functions.
- [ ] Run tests and require all 14 cases to pass without accessing server outcomes.

### Task 3: Freeze analysis execution

**Files:**
- Create: `freeze_analysis_execution_lock.py`
- Create: `ANALYSIS_EXECUTION_LOCK.json`

- [ ] Hash both frozen contracts and all core analyzer/validator files.
- [ ] Record `created_before_outcome_reveal=true` and `real_outcome_rows_read=0`.
- [ ] Compute deterministic `combined_analysis_execution_sha256` and copy the locked scripts to the task-owned server analysis directory.

### Task 4: Reveal once and lock primary result first

**Files:**
- Create: `formal_analysis_table_manifest.json`
- Create: `primary_result.json`
- Create: `PRIMARY_RESULT_LOCK.json`
- Create: `primary_tri_state.csv`
- Create: `primary_bootstrap.json`
- Create: `per_trial_primary.csv`

- [ ] Stream the 100 committed result artifacts and join them with their frozen captures without manually printing statuses.
- [ ] Reject any duplicate key, unresolved join, non-formal row, map/provenance mismatch, invalid status, or commitment mismatch.
- [ ] Write the server-only canonical table and a compact manifest.
- [ ] Compute and hash the immutable primary result before running secondary analysis.
- [ ] Run the exact 10,000-valid-replicate trial-cluster bootstrap with seed `20260831`.

### Task 5: Compute frozen secondary endpoints and figures

**Files:**
- Create: `secondary_endpoints.json`
- Create: `backend_usage.csv`
- Create: `multi_candidate_summary.json`
- Create: `selected_vs_nonselected_summary.json`
- Create: `scientific_interpretation.json`
- Create: `claim_boundary_audit.json`
- Create: `analysis_anomalies.csv`
- Create: `make_formal_analysis_figures.py`
- Create: `figures/*.png`

- [ ] Compute only the seven pre-registered secondary endpoints.
- [ ] Preserve UNKNOWN, exclude `u_des` as a native alternative, and generate no synthetic candidates.
- [ ] Produce 2–4 figures exclusively from locked compact summaries.
- [ ] Select the frozen decision case without post-hoc thresholds.

### Task 6: Validate, review, report, and publish

**Files:**
- Create: `reviewers/methods_statistics_review.json`
- Create: `reviewers/scientific_claim_review.json`
- Create: `FINAL_CASE_DECISION.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `DRAFT_PR_BODY.md`
- Create: `report/REPORT_ANALYZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1.md`

- [ ] Verify locked analyzer hashes remain unchanged and all protocol/formula/claim checks pass.
- [ ] Confirm no raw `.jsonl` or full canonical step table is staged.
- [ ] Complete the two bounded reviewer passes and the answer-first report.
- [ ] Stage only `reproduction/analysis/l2_h1_prospective_shadow_cohort_v1/`, commit, push, and create the Open Draft PR based on `collect-l2-h1-prospective-shadow-cohort-v1`.
