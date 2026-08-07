# Core Causal Architecture Specification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a frozen, non-implementation specification that separates Core V1's control-causal roles and selects exactly one conceptual follow-up.

**Architecture:** A task-owned generator freezes upstream PR and source-byte identities, creates role/state/evaluation documents from the position-first Euler contract, and emits a validator-backed Case A–E decision. No controller, method, map, data, or execution asset is imported or changed.

**Tech Stack:** Python standard library, Matplotlib for task-owned figures, Git/GitHub CLI identity checks, and read-only SSH GPU inspection.

---

### Task 1: Freeze upstream inputs

**Files:**
- Create: `reproduction/specification/core_causal_architecture_specification_v1/freeze_upstream_inputs.py`
- Create: `reproduction/specification/core_causal_architecture_specification_v1/input_freeze/pr*_identity.json`

- [ ] **Step 1: Write frozen PR identity checks**

```python
assert payload["state"] == "OPEN" and payload["isDraft"] is True
assert payload["headRefOid"] == expected_oid
```

- [ ] **Step 2: Verify protected raw Git blobs and write identity artifacts**

Run: `python -B reproduction/specification/core_causal_architecture_specification_v1/freeze_upstream_inputs.py`
Expected: `PASS_CORE_CAUSAL_UPSTREAM_FREEZE`

### Task 2: Build the role architecture and decision records

**Files:**
- Create: `architecture/*.md`, `architecture/*.csv`, `evaluation/*.md`, `evidence/*.csv`, `alternatives/*.md`, `reviews/*.md`, `decision/*.json`
- Test: `tests/test_protocol_outputs.py`

- [ ] **Step 1: Write the failing validator test**

```python
result = subprocess.run([sys.executable, "-B", str(ROOT / "validate_core_causal_architecture_spec.py")])
assert result.returncode == 0
```

- [ ] **Step 2: Materialize only frozen specification artifacts**

Run: `python -B reproduction/specification/core_causal_architecture_specification_v1/build_core_causal_architecture_spec.py`
Expected: `PASS_CORE_CAUSAL_ARCHITECTURE_ARTIFACTS_MATERIALIZED`

- [ ] **Step 3: Run proof, validation, and tests**

Run: `python -B reproduction/specification/core_causal_architecture_specification_v1/validate_core_causal_architecture_spec.py`
Expected: `PASS_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_VALIDATION`

### Task 3: Finalize bounded delivery

**Files:**
- Create: `report/REPORT_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1.md`
- Create: `report/DRAFT_PR_BODY.md`

- [ ] **Step 1: Run read-only GPU/watchdog inspection and validate final report parity**
- [ ] **Step 2: Copy only `REPORT*.md` to the report handoff path**
- [ ] **Step 3: Commit only this task directory and open a Draft PR based on PR #91**

## Self-review

- [ ] All prohibited operations remain at count zero.
- [ ] The formula check preserves position-first Euler and proves the zero/immediate versus nonzero/future derivatives.
- [ ] The decision has one case and one next task, and does not execute it.
