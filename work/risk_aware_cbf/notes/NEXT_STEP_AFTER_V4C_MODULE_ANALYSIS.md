# V4-C Trial-20 Recovery Failure Diagnosis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Diagnose the 34 original V4-C recovery failures concentrated in flight trial 20 using fixed-comparator replay and compact shadow counterfactuals, without changing recovery controls or HCE V0.

**Architecture:** A diagnosis runner temporarily observes original V4-C generation/evaluation during a formal original-comparator replay, retaining only compact derived activation fields and keeping earlier states in memory. It then evaluates preregistered search, horizon, and trigger shadows on comparator-derived representative contexts. A separate dynamics helper derives bounded position-deviation envelopes without claiming safety or controllability proof.

**Tech Stack:** Python 3.10 `safer_splat_official`, CUDA device 1, frozen V4-C helpers, compact CSV/JSON/Markdown artifacts.

---

### Task 1: Establish provenance and compact output schema

**Files:**
- Create: `work/risk_aware_cbf/results/v4c_trial20_failure_diagnosis/README.md`
- Create: `work/risk_aware_cbf/results/v4c_trial20_failure_diagnosis/preregistration.csv`

- [x] Create the isolated branch from `a83259798e0e4b1a2c7fcdce2617ebd8783ebcc3` and a restore checkpoint.
- [ ] Record the original H3_N128 comparator contract and mark every diagnostic as shadow-only.

### Task 2: Implement fixed-comparator replay observation

**Files:**
- Create: `work/risk_aware_cbf/scripts/run_v4c_trial20_failure_diagnosis.py`

- [ ] Hook only original generator/evaluator calls during trial-20 formal replay and retain exactly one compact derived row per activation.
- [ ] Assert 34 activations, 34 recovery failures, 34 executed-H violations, zero collision/QP infeasibility, and `stopped_before_goal` before running shadows.
- [ ] Build streak, family, representative-context, and original-family compact summaries without controls, raw state vectors, or per-step trajectories.

### Task 3: Implement bounded shadow diagnostics

**Files:**
- Create: `work/risk_aware_cbf/scripts/analyze_v4c_bounded_reachability.py`

- [ ] Evaluate only representative comparator-derived contexts under H3/N512, H3/CEM when parser-fixed, H4/N128, H5/N128, and earlier H3/N128 states in memory.
- [ ] Derive H1-H5 acceleration-bounded position-deviation envelopes, independent of collision geometry.
- [ ] Emit compact variant/hypothesis summaries and a unique redesign decision.

### Task 4: Report, verify, and publish

**Files:**
- Create: `work/risk_aware_cbf/REPORT_V4C_TRIAL20_RECOVERY_FAILURE_DIAGNOSIS.md`
- Modify: permitted V4-C materials and `REPRODUCIBILITY_MANIFEST.md`

- [ ] Verify all result artifacts are compact and forbidden/core paths are unchanged.
- [ ] Copy the final REPORT only to `C:\\Users\\zlab\\Desktop\\REPORT`, commit, push, and create the required Draft PR.
