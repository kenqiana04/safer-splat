# L2/H1 Prospective Shadow Cohort Protocol V1 Implementation Plan

> **For agentic workers:** Execute this plan inline, task by task. Do not dispatch subagents, run navigation, or collect formal data.

**Goal:** Freeze a deterministic, machine-readable official100 prospective shadow cohort protocol before any formal L2/H1 result exists.

**Architecture:** A task-local Python freezer reads only the frozen official100 CSV and PR #99 compact evidence, emits focused JSON/Markdown contracts, and computes a deterministic protocol lock over the contract bundle. A separate validator and unit tests independently check identity, cohort algebra, exclusion, join semantics, outcome-blind QC, retry rules, bootstrap configuration, and Git raw-log exclusion.

**Tech Stack:** Python 3 standard library, JSON, CSV, SHA-256, unittest, Git/GitHub CLI.

---

### Task 1: Freeze upstream and official100 identity

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/freeze_protocol.py`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/tests/test_protocol_contract.py`

- [ ] Add a test that parses the source CSV into exactly 100 unique integer IDs in stable order `0..99` and rejects duplicates or missing rows.
- [ ] Add a test that requires PR #99 head `17bec44c51207bf7f831db724e108b86adb0ace8` and source-manifest SHA-256 `1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344`.
- [ ] Implement canonical JSON serialization and raw-file SHA-256 helpers using only the Python standard library.
- [ ] Run `python -B -m unittest discover -s reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/tests -v`; expect the identity tests to pass.

### Task 2: Freeze cohort, run identity, and exclusion contracts

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_trial_manifest.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_run_id_schema.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_exclusion_contract.json`

- [ ] Generate 100 formal rows in integer order, each with data role `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1` and attempt-0 run ID `formal-v1-trial-{trial_id:03d}-attempt-0`.
- [ ] Require retry run IDs to increment only `attempt_id`, never replace a trial, and remain disjoint from PR #98/#99 QA namespaces.
- [ ] Hard-reject `EQUIVALENCE_QA_ONLY`, `PILOT_QA_ONLY`, `FROZEN_HISTORICAL_REPLAY`, and explicit PR #98/#99 QA run IDs.
- [ ] Test that pilot IDs `[10,30,50,70,90]` remain in formal100 but use fresh formal run IDs.

### Task 3: Freeze analysis and join semantics

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_analysis_contract.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_identity_join_contract.json`

- [ ] Encode the analysis unit as one committed selected/executed candidate-state-map tuple.
- [ ] Encode all ten primary eligibility predicates and preserve `SHADOW_RECOMPUTED_FROZEN_CERTIFIER` provenance.
- [ ] Freeze `N_primary = PASS + FAIL + UNKNOWN`, primary numerator `FAIL`, primary denominator including `UNKNOWN`, and the seven secondary endpoint families.
- [ ] Copy the final PR #99 capture/result identity checks: run ID, process-local trial token, step/state/decision/payload IDs, selected candidate ID, map authority ID, and semantic hashes.
- [ ] Freeze the denominator/control-trace join separately from the process-local token and forbid V1 hot fixes after first formal data.

### Task 4: Freeze QC, retry, environment, retention, and collection-lock contracts

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_qc_contract.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/outcome_blind_qc_contract.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_retry_stop_policy.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_artifact_retention_policy.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_collection_environment_contract.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_collection_lock_schema.json`

- [ ] Require every per-trial completeness rate to equal 1.0 and every instrumentation error count to equal zero.
- [ ] Permit collection-stage QC to check presence/type only; hard-deny aggregated PASS/FAIL/UNKNOWN and scientific endpoint summaries.
- [ ] Permit one fresh-process retry only for `PRE_DATA_INFRA_FAILURE` before the first intended step and before any capture/result/scientific row.
- [ ] Stop the cohort after any post-data failure, preserve partial evidence, and forbid automatic retry or replacement.
- [ ] Freeze physical GPU 1, map authority, runtime/controller/instrumentation identity, serial order, and nonadaptive collection.
- [ ] Define a collection-lock JSON schema requiring exactly 100 formal run IDs and protocol/map/environment/artifact identities without creating a real lock.

### Task 5: Freeze statistical and claim contracts

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/formal_claim_contract.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/FORMAL_COHORT_PROTOCOL.md`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/README.md`

- [ ] Freeze trial-cluster bootstrap with 100 clusters, 100 sampled clusters per replicate, 10,000 valid replicates, seed `20260831`, percentile 95% CI, and 100,000 maximum draws.
- [ ] Preserve UNKNOWN in the primary denominator; allow known-status sensitivity only as secondary.
- [ ] Freeze native multi-candidate provenance and `MULTI_CANDIDATE_ANALYSIS_NOT_ESTIMABLE` when no groups exist; synthetic candidate count remains zero.
- [ ] State the maximum supported mechanism-prevalence claim and all prohibited efficacy, collision, feasibility, real-time, and deployment claims.

### Task 6: Build deterministic protocol lock and validate it

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/PROTOCOL_LOCK.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/validate_formal_protocol_v1.py`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/validation_result.json`

- [ ] Hash every lockable protocol file by raw bytes and compute the combined SHA-256 over sorted path/hash records.
- [ ] Regenerate twice and assert byte-identical contracts and identical combined protocol SHA.
- [ ] Validate all twelve required tests, zero navigation/formal collection counts, raw-log Git exclusion, and exact PR #99 identity.
- [ ] Print exactly `PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1_VALIDATION` on success.

### Task 7: Review, report, and Git handoff

**Files:**
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/reviewers/methods_statistics_review.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/reviewers/systems_reproducibility_review.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/FINAL_CASE_DECISION.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/downstream_handoff.json`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/DRAFT_PR_BODY.md`
- Create: `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/report/REPORT_FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1.md`

- [ ] Record two short independent reviewer verdicts with no critical blockers and CASE_A only if every frozen gate passes.
- [ ] Write an answer-first technical report answering Q1–Q22 with exact definitions, limitations, and no meaningless chart.
- [ ] Recheck PR #99 identity, protocol SHA, unit tests, validator, `git diff --check`, staged paths, production diff, and raw-log exclusion.
- [ ] Stage only `reproduction/protocol/l2_h1_prospective_shadow_cohort_v1/`, commit, push, and create one Open Draft PR against the PR #99 branch.
- [ ] Stop without executing `COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`.
