# L2/H1 On-Policy Shadow Observation Design V1 Implementation Plan

> **For Codex:** Execute this plan in the current task only. The user has authorized design, static audit, validation, Git publication, and handoff; runtime instrumentation and collection remain prohibited.

**Goal:** Freeze a prospective, non-invasive, zero-authority L2/H1 shadow-observation protocol that closes the missing-control, reachability, candidate-provenance, and map-authority gaps found by PR #95 without changing or running the controller.

**Architecture:** Audit the frozen controller and certifier sources at PR #95, select a post-decision-commit immutable tap feeding a bounded nonblocking queue and isolated shadow worker, then define schemas, denominators, future equivalence/logging gates, claims, and implementation handoff. All artifacts live under this task directory; protected production sources remain byte-identical.

**Tech Stack:** Git/GitHub CLI, Python 3 standard library, JSON Schema documents, Markdown, CSV, and task-local deterministic validators.

---

### Task 1: Freeze upstream and protected source identity

**Files:**
- Create: `audit/upstream_pr_identity.json`
- Create: `audit/protected_source_start.json`
- Create: `audit/protected_source_end.json`

**Steps:**
1. Query PRs #83/#84/#86/#87/#89/#90/#91/#92/#93/#94/#95 read-only.
2. Require PR #95 to be Open Draft on `l2-h1-shadow-frozen-replay-v1` at `a7fd936804284a299467f1bfcc76deab12fdf0c3`, based on `l2-h1-shadow-certifier-v1`.
3. Recompute raw Git blob, byte size, and mode for every path in the upstream 17-blob protected manifest.
4. Stop on any identity drift; never follow a different upstream head.

### Task 2: Audit the frozen control-flow observation seams

**Files:**
- Create: `CONTROL_FLOW_OBSERVATION_SEAM_AUDIT.md`
- Create: `control_flow_observation_seams.json`
- Create: `frozen_replay_to_prospective_gap_mapping.csv`

**Steps:**
1. Trace `x_k`, `p_k`, `v_k`, `u_des`, selected `u_k`, `dt`, decision commit, plant update, map construction, and trial/step identity in frozen `run.py`.
2. Trace current-feasibility, swept-segment, unified candidate, native alternative, and result-object lifecycles in the frozen PR #84 and PR #89 sources.
3. Record exact paths and line numbers; do not infer a hook from prior prose.
4. Classify what the primary baseline exposes directly and what future instrumentation-only implementation must copy or evaluate in the zero-authority worker.

### Task 3: Freeze the prospective protocol and schemas

**Files:**
- Create: `README.md`
- Create: `ON_POLICY_SHADOW_OBSERVATION_PROTOCOL_V1.md`
- Create: `observation_architecture_comparison.csv`
- Create: `SELECTED_OBSERVATION_ARCHITECTURE.md`
- Create: `ZERO_AUTHORITY_CONTRACT.md`
- Create: `STATE_ACTION_ALIGNMENT_CONTRACT.md`
- Create: `prospective_step_schema.json`
- Create: `native_candidate_schema.json`
- Create: `map_authority_manifest_schema.json`
- Create: `observer_health_schema.json`
- Create: `reachability_reason_schema.json`
- Create: `PROSPECTIVE_DENOMINATOR_CONTRACT.md`
- Create: `prospective_analysis_plan.md`
- Create: `sample_size_and_stopping_rule.md`
- Create: `future_trial_manifest_policy.md`
- Create: `future_equivalence_gate_spec.md`
- Create: `future_logging_completeness_gate.md`
- Create: `future_validation_plan.md`
- Create: `kill_gates.json`
- Create: `claims_contract.md`

**Steps:**
1. Compare at least the post-commit tap, wrapper/decorator, and out-of-process sidecar architectures.
2. Select exactly one architecture and one fallback while preserving complete payload visibility and structural zero feedback.
3. Make selected `u_k`, reachability, map content identity, tri-state L2 status, instrumentation health, and same-decision IDs mandatory.
4. Separate executed primary cohort from native non-executed secondary cohorts and prohibit synthetic candidates/outcome-conditioned retention.
5. Freeze fixed-manifest primary stopping and a fixed-L2-reached fallback without fail-count stopping; use trial-cluster-aware uncertainty.

### Task 4: Validate mock serialization and obtain four independent design reviews

**Files:**
- Create: `fixtures/valid_step.json`
- Create: `fixtures/invalid_missing_u_k.json`
- Create: `reviewer/control_theory_review.json`
- Create: `reviewer/robotics_systems_review.json`
- Create: `reviewer/statistics_evaluation_review.json`
- Create: `reviewer/software_architecture_review.json`
- Create: `validate_on_policy_shadow_observation_design_v1.py`

**Steps:**
1. Validate a complete mock step and require the missing-`u_k` fixture to fail closed.
2. Run control-theory, robotics/systems, statistics/evaluation, and software-architecture review criteria independently.
3. Require no unresolved critical blockers and consistent recommended Case A before selecting Case A.
4. Run only task-local static/schema tests; do not import or execute the controller.

### Task 5: Finalize the decision, report, and handoff

**Files:**
- Create: `FINAL_CASE_DECISION.json`
- Create: `run_manifest.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `DRAFT_PR_BODY.md`
- Create: `report/REPORT_DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1.md`

**Steps:**
1. Answer the 20 required report questions directly at the report start.
2. Record all execution/mutation/collection counts as zero and classify evidence as design-only.
3. Re-run upstream PR #95 identity and the raw protected-source audit.
4. Run `python -B reproduction/design/l2_h1_on_policy_shadow_observation_v1/validate_on_policy_shadow_observation_design_v1.py` and require `PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_VALIDATION`.
5. Copy only the generated `REPORT*.md` to `C:/Users/zlab/Desktop/REPORT`.

### Task 6: Commit, push, and open the Draft PR

**Steps:**
1. Print `git status`, the exact staged file list, protected-source diff, production-source diff, and a fresh PR #95 identity query.
2. Stage only `reproduction/design/l2_h1_on_policy_shadow_observation_v1/`.
3. Commit exactly `docs(reproduction): design L2 H1 on-policy shadow observation`.
4. Push `design-l2-h1-on-policy-shadow-observation-v1` without force.
5. Open one Draft PR titled `[Draft] Design non-invasive on-policy L2/H1 shadow observation V1` against `l2-h1-shadow-frozen-replay-v1`.
6. Stop. Do not implement instrumentation or collect data.
