# L0 Shadow Certifier Semantics Diagnosis V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan inline and preserve the frozen, read-only scientific boundary. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain why every one of the 14,122 frozen formal prospective shadow records was classified `L0_BLOCKED`, without rerunning experiments or changing V1 evidence.

**Architecture:** Start from the exact PR #103 Git identity, lock the six compact diagnosis inputs, and inspect one formal result record only for schema. Trace the minimum L0 return-to-adapter-to-result path, stream the canonical table once only if a typed L0 outcome is actually logged, then freeze one Section 12 root class with a task-local validator.

**Tech Stack:** Git/GitHub CLI, Python standard library, JSON/CSV, `unittest`, frozen repository source.

---

### Task 1: Freeze upstream and compact inputs

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/L0_DIAGNOSIS_INPUT_LOCK.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/ROUTING_CORRECTION_NOTE.md`

- [ ] Verify PR #103 is Open Draft at `0b8e38e584c112eb778208e5c5933deb6adb23d0` and its remote branch matches.
- [ ] Hash the PR #103 diagnosis lock and the four frozen scientific locks from raw Git blob bytes.
- [ ] Read only the six allowed compact PR #103 files and record the frozen `14122`, `L0_BLOCKED=14122`, `L1 execution=0`, and `L2 execution=0` facts.
- [ ] Write the input lock with both mutation authorities set to false and document the L1-to-L0 routing correction without altering PR #103.

### Task 2: Test the L0 mapping model first

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/tests/test_l0_semantics.py`
- Create or modify: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/aggregate_l0_outcomes.py` only if typed outcomes are observable.

- [ ] Write exactly five synthetic tests: PASS mapping, FAIL mapping, UNKNOWN mapping, mapping mismatch detection, and non-fabrication when L0 outcome is absent.
- [ ] Run `python -B -m unittest discover -s reproduction/diagnosis/l0_shadow_certifier_semantics_v1/tests -p 'test_*.py' -v` and confirm the implementation import initially fails.
- [ ] Implement only the pure mapping/aggregation helpers needed by those tests if the frozen schema exposes typed outcomes.
- [ ] Rerun the five tests and require all to pass.

### Task 3: Establish L0 observability before aggregation

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/l0_observability_inventory.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/l0_outcome_summary.json`
- Conditionally create: `l0_status_distribution.csv`, `l0_reason_distribution.csv`, `l0_backend_distribution.csv`

- [ ] Inspect the result schema, payload/result dataclass, and exactly one canonical formal result record for field names and types.
- [ ] Record whether status, reason, backend, query status, and input identity are logged.
- [ ] If typed L0 status is present, stream the canonical table exactly once and require category counts to sum to 14,122.
- [ ] If typed L0 status is absent, emit `L0_OUTCOME_DISTRIBUTION_NOT_OBSERVABLE_FROM_FROZEN_RESULTS` and do not scan or infer FAIL/UNKNOWN counts.

### Task 4: Trace mapping, semantics, and authority gating

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/l0_status_mapping_audit.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/l0_semantics_summary.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/authority_observability_gating_audit.json`
- Conditionally create: `historical_prospective_l0_bridge.json`

- [ ] Use `git grep -n` for `L0_BLOCKED`, the actual L0 status field, certifier function/type, and result type.
- [ ] Open no more than five relevant functions and capture file, function, exact condition, return type, PASS token, exception/default behavior, and semantic consequence.
- [ ] Read only the smallest frozen spec excerpts needed to define current-state/segment, Start-Safe/admission/repair, PASS/FAIL/UNKNOWN, map authority, and candidate dependence.
- [ ] Compare controller-authority gating with shadow-observation gating and classify implementation conformance.
- [ ] Read at most one historical compact summary and one historical adapter excerpt only if prospective evidence cannot establish the mapping/gating relation.

### Task 5: Freeze the root class and reviewer result

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/root_cause_diagnosis.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/l0_semantics_diagnosis_review.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/FINAL_CASE_DECISION.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/downstream_handoff.json`

- [ ] Select exactly one L0-S1 through L0-S8 class from preserved evidence, without preferring a positive outcome.
- [ ] Bind the only next task exactly to the selected class.
- [ ] Write one reviewer JSON of at most 600 Chinese characters covering status semantics, mapping, authority separation, unchanged V1 Case C, and next-task determinism.

### Task 6: Validate and report

**Files:**
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/validate_l0_semantics_diagnosis_v1.py`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/validation_result.json`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/README.md`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/DRAFT_PR_BODY.md`
- Create: `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/report/REPORT_DIAGNOSE_L0_SHADOW_CERTIFIER_SEMANTICS_V1.md`

- [ ] Implement validator checks for upstream identity, locks, frozen counts, observability evidence, mapping source evidence, gating spec evidence, root-class consistency, task-only changes, zero experiment/runtime mutation, zero V1 reinterpretation, and no raw logs.
- [ ] Run JSON parsing, exactly five tests, validator, and `git diff --check`; require `PASS_L0_SHADOW_CERTIFIER_SEMANTICS_DIAGNOSIS_V1_VALIDATION`.
- [ ] Put the eight answer-first conclusions at the beginning of the report and disclose any non-observability limitation.

### Task 7: Commit and create the Draft PR

- [ ] Recheck PR #103 and raw upstream identities immediately before staging.
- [ ] Stage only `reproduction/diagnosis/l0_shadow_certifier_semantics_v1/` and print the exact staged file list.
- [ ] Commit with `diagnosis(reproduction): isolate frozen shadow L0 admission semantics`.
- [ ] Push `diagnose-l0-shadow-certifier-semantics-v1` and create one Open Draft PR based on `diagnose-l2-h1-primary-reachability-v1`.
- [ ] Recheck remote head, Draft state, clean worktree, final validator, and copy only the generated `REPORT*.md` to the standing Desktop report directory.
