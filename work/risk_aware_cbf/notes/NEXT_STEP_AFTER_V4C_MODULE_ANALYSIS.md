# R-V4C-6 GTEP Shadow Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate a fixed geometry-conditioned tangential primitive bank only as a shadow counterfactual on all 34 original trial-20 activation states.

**Architecture:** A read-only adapter invokes the existing ball-to-ellipsoid analytic `h` and position gradient. An equivalence checker verifies source/adapter values and state isolation before a fixed primitive bank uses the original clamp, dynamics, and GSplat query for H3 rollouts; H5 is diagnostic-only and conditional.

**Tech Stack:** Python 3.10 `safer_splat_official`, CUDA device 1, frozen GSplat/V4-C utilities, compact CSV/JSON/Markdown artifacts.

---

### Task 1: Barrier semantics and adapter

**Files:**
- Create: `work/risk_aware_cbf/paper_materials/GTEP_BARRIER_GEOMETRY_SEMANTICS_AUDIT.md`
- Create: `work/risk_aware_cbf/scripts/gsplat_barrier_geometry_adapter.py`
- Create: `work/risk_aware_cbf/scripts/check_gtep_geometry_equivalence.py`

- [x] Confirm the existing ball-to-ellipsoid path returns analytic position gradients.
- [ ] Wrap the existing query without changing `h`, check its gradient/normal/critical index and state isolation on preregistered contexts.

### Task 2: Fixed primitive bank and shadow evaluator

**Files:**
- Create: `work/risk_aware_cbf/scripts/v4c_geometry_tangential_primitives.py`
- Create: `work/risk_aware_cbf/scripts/run_v4c_gtep_shadow_audit.py`

- [ ] Generate no more than 24 deterministic clamped P0-P6 candidates per context from the verified analytic normal.
- [ ] Replay original trial-20 controls solely to obtain the 34 formal states, and shadow-evaluate the fixed bank with original dynamics/query semantics.
- [ ] Emit compact family, progress, critical-ID, isolation, positive-control, and conditional H5 summaries.

### Task 3: Report and publication

**Files:**
- Create: `work/risk_aware_cbf/REPORT_V4C_GTEP_SHADOW_FEASIBILITY.md`
- Modify: permitted V4-C materials and `REPRODUCIBILITY_MANIFEST.md`

- [ ] Validate no raw or forbidden artifacts, copy REPORT to the desktop REPORT directory, commit, push, and create the draft PR.
