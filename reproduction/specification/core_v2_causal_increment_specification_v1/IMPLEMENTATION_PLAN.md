# Core V2 L2/H1 Causal Increment Specification V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an auditable, falsifiable, specification-only decision for the minimal L2/H1 causal increment without implementing Core V2 or running a formal method.

**Architecture:** Freeze PR #83–#92 and the 17 PR #92 protected blobs, derive H1 control authority from the frozen position-first Euler contract, and audit whether the frozen Gaussian segment backend can serve a distinct L2 causal role. Materialize only Markdown/JSON/CSV/PNG evidence plus deterministic validators inside this task directory.

**Tech Stack:** Python standard library, Git/GitHub CLI read-only identity checks, Matplotlib for task-owned figures, unittest, and SSH/NVIDIA read-only state queries.

---

### Task 1: Freeze authority and protected sources

**Files:**
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/task_config.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/freeze_upstream_inputs.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/FROZEN_UPSTREAM_IDENTITY.json`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/PROTECTED_SOURCE_AUDIT.json`

- [ ] Verify PR #92 is Open Draft at `dfd9bce2633e542fdb72a1805f79cc4feeeebc3a`.
- [ ] Verify PR #83/#84/#86/#87/#89/#90/#91 remain Open Draft at their frozen heads.
- [ ] Recompute all 17 raw Git blob identities and SHA-256 values.
- [ ] Freeze supplemental backend and timing source identities separately from the protected count.

### Task 2: Verify control authority

**Files:**
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/verify_h1_control_authority.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/CONTROL_AUTHORITY_H1_DERIVATION.md`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/control_authority_h1_derivation.json`

- [ ] Check `p_(k+1)`, `v_(k+1)`, `p_(k+2)`, and `p_H1(alpha)` symbolically.
- [ ] Check finite-difference Jacobians at `alpha=0,0.25,0.5,1`.
- [ ] Verify `u_(k+1)` cannot affect the frozen H1 position segment.
- [ ] Fail closed on any indexing or endpoint inconsistency.

### Task 3: Audit frozen geometry and semantics

**Files:**
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/build_core_v2_spec.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/H1_SEGMENT_CONTRACT.md`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/L2_PREDICATE_CONTRACT.md`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/map_safety_semantics_audit.json`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/continuous_segment_semantics_audit.json`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/execution_optimizer_verifier_consistency.json`

- [ ] Classify exact sphere, conservative interval, and sampled diagnostic backends.
- [ ] Freeze map snapshot, represented-obstacle, robot footprint, margin, UNKNOWN, nonfinite, and missing-geometry semantics.
- [ ] Define tri-state L2 input/output without adding a new geometry primitive.
- [ ] Prove geometry-backend reuse is distinct from B1 causal-role reuse.

### Task 4: Specify bounded architecture delta and falsification

**Files:**
- Create: all remaining required Markdown/JSON/CSV contracts, four reviewer JSON files, and ten required figures in this task directory.

- [ ] Preserve L0/L1/L3/L4/L5 and define only the L2/H1 delta.
- [ ] Preserve the frozen 11-type taxonomy and map L2 outcomes onto it.
- [ ] Define L2 denominators without generating prevalence numbers.
- [ ] Resolve G1–G7 independently of the final case.
- [ ] Run four scoped adversarial reviews before writing `FINAL_CASE_DECISION.json`.

### Task 5: Validate and deliver

**Files:**
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/validate_core_v2_causal_increment_spec.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/tests/test_protocol_outputs.py`
- Create: `reproduction/specification/core_v2_causal_increment_specification_v1/report/REPORT_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1.md`

- [ ] Run compileall, unittest, optional pytest, Git diff checks, credential/large-asset checks, and the fail-closed validator.
- [ ] Perform final read-only GPU 1 and watchdog/SSH preservation checks.
- [ ] Mirror only compact report/audit evidence to the task-owned server maintenance root.
- [ ] Stage only this directory, commit with the frozen message, push, and create one Open Draft PR against `core-causal-architecture-specification-v1`.
- [ ] Stop without executing the selected `Only next task`.
