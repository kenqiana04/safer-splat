# R-V4C-1 Hierarchical Candidate Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate a two-stage V4-C recovery wrapper on fixed flight trials 12, 13, and 14 while preserving original candidate, cost, seed, and fallback semantics.

**Architecture:** The evaluator will call the original V4-C generator and evaluator twice at most: a copied Namespace with `num_sequences=0` and `use_cem=False` for deterministic Stage A, followed by the untouched original args for Stage B only when Stage A has no feasible candidate. The paired audit keeps original V4-C in control of the formal trajectory; active A/B invokes the original `run_trial` with a temporary evaluator hook and discards all raw writer rows.

**Tech Stack:** Python 3.10 `safer_splat_official`, CUDA device 1, original V4-C helpers, compact CSV/JSON/Markdown outputs.

---

### Task 1: Preregister exact comparator configuration

**Files:**
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/preregistration.csv`
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/configuration.csv`
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/README.md`

- [x] Record the six fixed active runs in order `12/original`, `12/hierarchical`, `13/hierarchical`, `13/original`, `14/original`, `14/hierarchical`.
- [ ] Record provenance-confirmed H3_N128 arguments: H=3, N=128, on-margin trigger, dt margin 0.0005, warning margin 0.0008, dt 0.05, max steps 800, three deterministic family flags true, CEM false, original weights, and StartGuard projection path.

### Task 2: Implement evaluator and family classifier

**Files:**
- Create: `work/risk_aware_cbf/scripts/v4c_hierarchical_candidate_evaluator.py`
- Create: `work/risk_aware_cbf/scripts/v4c_candidate_family_metrics.py`

- [x] Build `HierarchicalEvaluationResult` with Stage A/B counts, timing, selected result, and family summary.
- [ ] Use this Stage-A construction without changing other args:

```python
stage_a_args = copy.deepcopy(original_args)
stage_a_args.num_sequences = 0
stage_a_args.use_cem = False
```

- [x] Call original `generate_sequences` and `evaluate_sequences`; enter Stage B only when Stage-A `recovery_success` is false.
- [x] Map exact source labels to baseline, braking, repulsive, goal-directed, continuity, random, cem, or unknown.

### Task 3: Implement and run contract checks

**Files:**
- Create: `work/risk_aware_cbf/scripts/check_v4c_hierarchical_contract.py`
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/contract_check.csv`

- [x] Test that Stage A has no random/CEM source, does not mutate state/args, and calls original selection semantics.
- [x] On a real fixed context, compare Stage-B full generator/evaluator output to direct original output: source list, selected index/source/first control/H sequence/minimum H/success/failure and RNG state.
- [x] Stop before trials if any critical row fails.

### Task 4: Implement compact paired and active runners

**Files:**
- Create: `work/risk_aware_cbf/scripts/run_v4c_hierarchical_paired_audit.py`
- Create: `work/risk_aware_cbf/scripts/run_v4c_hierarchical_active_ab.py`

- [x] Use original `run_trial` with null writers so no per-step, sequence, recovery, or trials CSV is written.
- [x] Run original trajectory plus hierarchical shadow at identical activation context for paired audit.
- [x] Gate active A/B on zero paired feasibility/safety regression and positive paired median runtime reduction.
- [x] Run active A/B sequentially in preregistered order, with a nonformal warm-up before measurements.

### Task 5: Aggregate, report, and freeze decision

**Files:**
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/*.csv`
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/metrics.json`
- Create: `work/risk_aware_cbf/results/v4c_hierarchical_candidate_evaluation_v0/analysis_notes.md`
- Create: `work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_CANDIDATE_EVALUATION_V0.md`
- Modify: permitted V4-C paper/decision materials and `REPRODUCIBILITY_MANIFEST.md`

- [x] Emit only compact aggregate result files, determine `r_v4c1_decision`, and state negative/neutral evidence.
- [ ] Verify no forbidden source, raw artifact, trace, image, model, or binary is modified; commit and create the specified Draft PR.
