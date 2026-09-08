# Full Active Runtime Pre-Repair Architecture Audit V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete an audit-until-complete, CPU/static pre-repair audit of PR #123 against PR #107–#123 without changing runtime or executing real ACTIVE.

**Architecture:** Freeze PR #123 identities and an A–Q domain manifest, then mechanically inspect the 17 runtime modules, frozen contracts, transition table, and public-cycle implementation. Deterministic probes and existing CPU tests may record findings, but every domain is completed even after defects; repair is only planned in a bounded DAG.

**Tech Stack:** Python `ast`/`unittest`, CSV/JSON manifests, Git/GitHub CLI, no GPU or scientific oracle.

---

### Task 1: Freeze audit inputs and domain scope

**Files:**
- Create: `reproduction/audit/active_runtime_pre_repair_architecture_v2/FULL_PRE_REPAIR_AUDIT_INPUT_LOCK.json`
- Create: `reproduction/audit/active_runtime_pre_repair_architecture_v2/AUDIT_DOMAIN_MANIFEST_V2.json`
- Create: `reproduction/audit/active_runtime_pre_repair_architecture_v2/build_pre_repair_audit_harness_v2.py`

- [ ] Verify PR #123 is the exact Open Draft and record all PR #107–#123 authority artifact hashes.
- [ ] Record all current runtime blobs, PR119 bypass evidence, PR120 blocker, and PR123 first-counterexample identity.
- [ ] Freeze A–Q as complete-required domains and set all execution counters to zero.
- [ ] Run the builder and check that every locked artifact exists and hashes deterministically.

### Task 2: Run complete static/domain audits

**Files:**
- Create: the A–Q CSV/JSON audit outputs listed in the task specification.
- Create: `reproduction/audit/active_runtime_pre_repair_architecture_v2/model_check_active_runtime_pre_repair_v2.py`

- [ ] Parse every runtime module and extract ownership, branches, event encoders, identities, numeric literals, and side-effect calls.
- [ ] Compare every frozen transition row across FrozenRow, TransitionRule, and RoutingDecision; enumerate overlap and destination-derived metadata risks.
- [ ] Build observed phase/event graphs and audit deadline, alternative, backup, terminal, exception, UNKNOWN, start, arbitration, commit, trace, lifecycle, BYPASS, legacy, and oracle semantics.
- [ ] Enumerate symbolic runtime states and at least 40 deterministic adversarial CPU probes; continue all domains after any defect.
- [ ] Run applicable existing CPU tests without real ACTIVE, GPU, smoke, oracle, or official100.

### Task 3: Register findings and repair DAG

**Files:**
- Create: `MASTER_DEFECT_REGISTER_V2.csv`, `LATENT_HIGH_RISK_REGISTER_V2.csv`, `VERIFIED_NOT_A_BUG_REGISTER_V2.csv`
- Create: `DEFECT_ROOT_CAUSE_CLUSTERING_V2.json`, `PRE_REPAIR_REPAIR_DAG_V2.json`, `FULL_ARCHITECTURE_AUDIT_INVARIANTS_V2.json`

- [ ] Classify every finding as `CONFIRMED_DEFECT`, `LATENT_HIGH_RISK`, or `VERIFIED_NOT_A_BUG` with frozen evidence.
- [ ] Cluster defects by common root cause and choose a single bounded repair strategy or explicit staged DAG.
- [ ] Define preregistered repair tests and preserve the rule that no repair occurs in this task.

### Task 4: Validate, review, and publish

**Files:**
- Create: `validate_full_active_runtime_pre_repair_audit_v2.py`, `validation_result.json`, reviewer, decision, handoff, PR body, and report.
- Create: `FULL_PRE_REPAIR_AUDIT_EXECUTION_LOCK.json` before substantive audits.

- [ ] Validate exact PR123 identity, runtime diff zero, A–Q completion, findings, symbolic model, 40+ probes, and zero real-execution counters.
- [ ] Run `git diff --check`, verify only the task directory is staged, and confirm no protected/runtime source changed.
- [ ] Commit as `audit(reproduction): freeze full active runtime pre-repair audit V2` and `validation(reproduction): freeze full pre-repair architecture findings V2`.
- [ ] Push `audit-active-runtime-pre-repair-architecture-v2`, open one Draft PR against `revalidate-active-runtime-contract-conformance-v2`, and stop without repair/revalidation/smoke.

### Self-review

- [ ] Every A–Q domain is `COMPLETE` or `BLOCKED_BY_MISSING_ARTIFACT`, never stopped because of a prior defect.
- [ ] Findings distinguish confirmed defects from latent risks and verified non-bugs.
- [ ] Runtime/protected/production diff remains zero and no scientific data is created or reinterpreted.
- [ ] The downstream handoff names only the bounded repair node; no repair is executed automatically.
