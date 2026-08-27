# L2/H1 Frozen Historical Replay Validation V1 Implementation Plan

> **For agentic workers:** Execute this plan inline and task-by-task. Do not delegate or run any downstream task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the PR #94 shadow-only L2/H1 certifier against a source universe frozen from pre-existing historical state-candidate-map evidence without generating state, candidates, maps, or controller actions.

**Architecture:** A task-local inventory layer first freezes every eligible historical source before any L2 result is computed. A replayability layer then separates formal, diagnostic, and non-replayable rows; only architecture-reached formal rows are passed to the imported PR #94 implementation. Deterministic aggregation, differential checks, reviewer audits, and a fail-closed validator produce compact evidence without modifying upstream science code.

**Tech Stack:** Python standard library, NumPy already required by PR #94, Git raw-object plumbing, CSV/JSON/JSONL, unittest, matplotlib only if already available, GitHub CLI, read-only SSH.

---

### Task 1: Freeze upstream and protected identities

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/audit/upstream_identity.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/audit/protected_source_audit.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/freeze_upstream.py`

- [ ] Verify PR #94 is Open Draft with base `core-v2-causal-increment-specification-v1`, head `l2-h1-shadow-certifier-v1`, and SHA `9bffdd2db585974ee61684cebfc99229aa52c47c`.
- [ ] Verify PR #83-#94 states and exact recorded heads.
- [ ] Read the PR #94 protected manifest and validate each blob with `git cat-file`, including blob id, byte size, mode, and SHA-256.
- [ ] Run `python -B freeze_upstream.py`; expect `PASS_FROZEN_REPLAY_UPSTREAM_FREEZE`.

### Task 2: Inventory and freeze the source universe before replay

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/inventory_sources.py`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/source_inventory.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/source_inventory.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/source_universe_freeze.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/FROZEN_REPLAY_PROTOCOL.md`

- [ ] Enumerate only PR #83-#94 artifacts and exact upstream-referenced maintenance paths; do not scan unrelated server storage.
- [ ] Record for every possible source whether it contains run/trial/step, `p_k`, `v_k`, `u_k`, `dt`, candidate identity, map identity/hash, robot contract, L1/B1, reachability, and backend context.
- [ ] Define `N_all` from all candidate-state-map rows in the frozen inventory without examining L2 output.
- [ ] Write a source-universe semantic hash over canonical source identities and freeze timestamp/order.
- [ ] Run `python -B inventory_sources.py --freeze-only`; expect `PASS_SOURCE_UNIVERSE_FROZEN_BEFORE_REPLAY`.

### Task 3: Build typed replayability and reachability manifests

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/build_replay_manifest.py`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replayability_audit.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replayability_reason_breakdown.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/architecture_reachability_audit.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/frozen_replay_manifest.jsonl`

- [ ] Write failing tests proving missing pre-call evidence maps to `NOT_REPLAYABLE`, never `L2_UNKNOWN`.
- [ ] Classify each frozen row as `FORMAL_REPLAYABLE`, `DIAGNOSTIC_RECONSTRUCTABLE`, or `NOT_REPLAYABLE` before any certifier call.
- [ ] Record `l2_reached` independently from mechanical replayability using only stored historical architecture evidence.
- [ ] Separate executed/selected from logged non-executed historical candidates.
- [ ] Canonicalize each row identity and produce deterministic surrogate candidate ids only when the historical numeric candidate is already uniquely fixed.
- [ ] Run manifest tests; expect stable row counts and hashes.

### Task 4: Execute imported PR #94 frozen replay

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/run_frozen_replay.py`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replay_results.jsonl`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replay_results.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replay_summary.json`

- [ ] Import `l2_h1_shadow_certify` directly from `reproduction/shadow/l2_h1_shadow_certifier_v1`; do not copy or simplify the certifier.
- [ ] Gate every formal row for finite values, dimensions, `dt`, candidate, map, robot contract, backend, and query authority.
- [ ] Evaluate only architecture-reached formal rows for primary L2 counts; label mechanically replayable non-reached rows diagnostic only.
- [ ] Persist PASS/FAIL/UNKNOWN exactly as returned by PR #94 and keep pre-call missingness outside UNKNOWN.
- [ ] Run one deterministic full replay batch on CPU when possible; record operational wall time only, not as a formal runtime metric.

### Task 5: Test determinism and differential fidelity

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replay_determinism_audit.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/replay_differential_integrity_audit.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/tests/`

- [ ] Repeat the frozen manifest replay and compare semantic row identities, statuses, reasons, H1 endpoints, formal values, and backend identities.
- [ ] Select spot-check rows by a pre-frozen stable-sort/hash rule.
- [ ] Independently reconstruct `p_k1` and `p_k2`, call the frozen backend, and compare against the imported PR #94 result.
- [ ] Run `python -B -m unittest discover -s tests -v`; expect all tests PASS.

### Task 6: Produce denominator, increment, multi-candidate, and missingness evidence

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/denominator_audit.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/stored_l1_vs_l2_crosstab.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/recomputed_diagnostic_l1_vs_l2_crosstab.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/l2_information_increment_summary.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/l2_unknown_reason_breakdown.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/l2_unknown_by_source.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/multi_candidate_group_analysis.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/coverage_by_source.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/coverage_by_run.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/coverage_by_trial.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/missingness_reason_by_source.csv`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/selection_bias_audit.md`

- [ ] Audit raw count identities before percentages.
- [ ] Keep stored L1 and recomputed diagnostic L1 completely separate; emit `NOT_ESTIMABLE` when stored L1 is absent.
- [ ] Compute L1 PASS/L2 FAIL only over architecture-reached evaluated rows and describe it only as information increment.
- [ ] Analyze multiple candidates only when multiple historical candidates share the same frozen state/map group.
- [ ] Disclose source/run/trial missingness and use `MISSINGNESS_MECHANISM_NOT_IDENTIFIED` when randomness cannot be established.

### Task 7: Review claims and select exactly one case

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/reviewers/control_theory_review.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/reviewers/robotics_systems_review.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/reviewers/statistics_evaluation_review.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/reviewers/software_reproducibility_review.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/FINAL_CASE_DECISION.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/claim_boundary.md`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/historical_evidence_non_upgrade_audit.json`

- [ ] Run four independent checklist reviews against frozen evidence.
- [ ] Select CASE_A only when valid replay observes a preregistered L2-specific increment; select CASE_E when valid replay observes none; otherwise select the corresponding fail-closed blocker case.
- [ ] Prohibit collision prevention, efficacy, recursive feasibility, deployment, real-time, and physical-world safety claims.

### Task 8: Validate, report, mirror, and publish

**Files:**
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/validate_l2_h1_frozen_replay_v1.py`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/validation_result.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/run_manifest.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/downstream_handoff.json`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/DRAFT_PR_BODY.md`
- Create: `reproduction/replay/l2_h1_shadow_frozen_replay_v1/report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md`

- [ ] Run compileall, unittest, pytest if installed, Git diff checks, credential scan, large-asset scan, upstream identity refresh, protected raw-object refresh, and denominator checks.
- [ ] Expect validator status `PASS_L2_H1_FROZEN_REPLAY_V1_VALIDATION` for a valid replay case.
- [ ] Copy only compact task evidence to `/disk1/zlab/maintenance_records/l2_h1_shadow_frozen_replay_v1` and verify SHA-256 identities.
- [ ] Stage only `reproduction/replay/l2_h1_shadow_frozen_replay_v1/` and audit the exact staged list.
- [ ] Commit exactly `analysis(reproduction): validate L2 H1 shadow certifier on frozen replay`.
- [ ] Push `l2-h1-shadow-frozen-replay-v1` and create the specified Open Draft PR based on `l2-h1-shadow-certifier-v1`.
