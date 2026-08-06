# SAFER-Splat Research Direction Due-Diligence V1 Implementation Plan

> **For agentic workers:** Execute this plan inline and preserve the frozen candidate, scoring, evidence, and stop-gate contracts. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a source-traceable, falsifiable decision on whether exactly one SAFER-Splat/FAS-CBF research direction is novel, data-ready, and deliverable within eight weeks, without training or method implementation.

**Architecture:** The audit is evidence-first. Canonical Git blobs freeze prior work; a two-round primary-source review builds the competitor matrix; a read-only map/reference inventory determines evaluability; and a preregistered scoring plus fatal-gate layer produces one of Cases A–E. A validator recomputes identities, counts, score arithmetic, gate logic, claim-source coverage, and no-execution boundaries from committed artifacts.

**Tech Stack:** Git/GitHub CLI, Python 3 standard library, CSV/JSON/Markdown, Matplotlib, pytest, primary-source web and arXiv evidence.

---

### Task 1: Freeze lineage and contracts

**Files:**
- Create: `task_config.py`
- Create: `freeze_upstream_inputs.py`
- Create: `input_freeze/pr84_identity.json`
- Create: `input_freeze/pr85_identity.json`
- Create: `input_freeze/pr86_identity.json`
- Create: `input_freeze/pr87_identity.json`
- Create: `input_freeze/protected_source_hashes.json`

- [ ] Verify PR #84–#87 state, draft status, base/head branches, and exact heads against GitHub and local canonical objects.
- [ ] Freeze D0–D8 before scoring, the 14 positive dimensions, 10 risk dimensions, fixed weights, thresholds, fatal gates, event-query ceilings, and execution prohibitions in `task_config.py`.
- [ ] Hash canonical upstream trees without reading mutable working-tree copies.
- [ ] Record any task-only infrastructure action in `audits/operational_autonomy_actions.json`.

### Task 2: Build the historical evidence ledger

**Files:**
- Create: `history/workstream_ledger.csv`
- Create: `history/evidence_asset_inventory.csv`
- Create: `history/falsified_hypotheses.csv`
- Create: `history/reusable_artifact_manifest.json`
- Create: `history/claim_boundary_registry.csv`
- Create: `history/timeline.md`

- [ ] Enumerate R1–R12 from all relevant refs and canonical report blobs.
- [ ] Separate positive evidence, negative evidence, falsified hypotheses, reusable assets, non-claims, and sunk cost.
- [ ] Preserve the activated-cohort mechanism pass and representative-holdout 0/160 limitation as simultaneous truths.

### Task 3: Execute the systematic primary-source review

**Files:**
- Create: `literature/search_protocol.md`
- Create: `literature/search_queries.csv`
- Create: `literature/screening_log.csv`
- Create: `literature/included_papers.csv`
- Create: `literature/excluded_papers.csv`
- Create: `literature/snowballing_log.csv`
- Create: `literature/source_archive_manifest.json`
- Create: `literature/fulltext_evidence_matrix.csv`
- Create: `literature/baseline_availability.csv`
- Create: `literature/claim_to_source_map.json`
- Create: `literature/competitor_cards/*.md`

- [ ] Run Round A high-recall searches for L1–L24 across primary academic sources through 2026-08-06.
- [ ] Run Round B backward/forward snowballing from the closest Gaussian-navigation, Gaussian-CBF, uncertainty, learned-map safety, and sampled-data/backup-filter papers.
- [ ] Deduplicate by DOI/arXiv/title identity and preserve all exclusion reasons.
- [ ] Read full text for high-relevance papers and record page, section, theorem, figure, table, and official-code pointers.
- [ ] Treat absence claims as unverified unless paper, supplement, and official code were all searched.

### Task 4: Audit data, references, and event rates

**Files:**
- Create: `data/map_readiness_matrix.csv`
- Create: `data/reference_authority_matrix.csv`
- Create: `data/query_event_rate_contract.md`
- Create: `data/query_event_rate_records.csv`
- Create: `data/event_rate_summary.csv`
- Create: `data/split_feasibility.csv`
- Create: `data/data_blockers.json`

- [ ] Freeze deterministic sampling before reading event outcomes.
- [ ] Audit M1–M9 from frozen artifacts; mark missing reference or identity as `NOT_EVALUABLE`.
- [ ] Reuse existing locked query records where they satisfy the sampling contract; never retrain, retune, mutate, or run navigation.
- [ ] Report event prevalence, label authority, leakage risk, and cross-map split feasibility separately.

### Task 5: Define and score all directions

**Files:**
- Create: `candidates/candidate_direction_registry.json`
- Create: `candidates/direction_cards/*.md`
- Create: `feasibility/asset_dependency_graph.json`
- Create: `feasibility/effort_estimates.csv`
- Create: `feasibility/eight_week_critical_path.csv`
- Create: `feasibility/external_dependency_risks.csv`
- Create: `scoring/scoring_contract.json`
- Create: `scoring/positive_scores.csv`
- Create: `scoring/risk_scores.csv`
- Create: `scoring/net_scores.csv`
- Create: `scoring/fatal_gate_audit.csv`

- [ ] State each D0–D8 problem, I/O, novelty sentence, competitors, minimum method/theory/experiments, data/reference needs, fallback, and fatal risk.
- [ ] Estimate best/likely/worst work, GPU hours, storage, dependencies, and an eight-week critical path.
- [ ] Score every direction under the frozen arithmetic; do not let scores override fatal gates.

### Task 6: Run adversarial review and decide

**Files:**
- Create: `reviews/*/*.md`
- Create: `reviews/reviewer_score_matrix.csv`
- Create: `reviews/disagreement_analysis.md`
- Create: `decision/venue_fit_matrix.csv`
- Create: `decision/submission_timeline.md`
- Create: `decision/anti_drift_contract.md`
- Create: `decision/final_direction_decision.json`
- Create: `decision/frozen_problem_statement.md`
- Create: `decision/frozen_eight_week_plan.md`
- Create: `decision/two_week_falsifiability_gate.md`

- [ ] Select the top three by net score without disclosing the final recommendation to the four reviewer-role passes.
- [ ] Produce novelty, theory, systems, and data reviews with independent criteria and recommendations.
- [ ] Apply Cases A–E exactly; select no new method if no direction passes every hard gate.
- [ ] Freeze venue fit, non-claims, unresolved evidence, next task, and anti-drift rules.

### Task 7: Build figures, validate, and publish

**Files:**
- Create: `figures/*.png`
- Create: `audits/*.json`
- Create: `validate_direction_audit.py`
- Create: `report/validation_result.json`
- Create: `report/downstream_handoff.json`
- Create: `report/REPORT_AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md`
- Create: `report/DRAFT_PR_BODY.md`

- [ ] Generate all 24 required figures with source-class and non-performance labels.
- [ ] Validate lineage, hashes, counts, literature evidence, score arithmetic, gates, decision case, no-execution boundaries, and artifact consistency.
- [ ] Run `python -m compileall`, scoped `pytest`, validator, `git diff --check`, credential/large-file scan, GPU/process read-only check, and watchdog/SSH preservation check.
- [ ] Stage only `reproduction/research_direction/safer_splat_direction_audit_v1`, commit with the authorized message, push the frozen branch, and open one Draft PR against PR #87 head branch.
- [ ] Copy only the final `REPORT*.md` file to `C:\Users\zlab\Desktop\REPORT` and verify byte identity.
