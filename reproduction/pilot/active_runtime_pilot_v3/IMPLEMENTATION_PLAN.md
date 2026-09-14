# Active Runtime Pilot V3 Protocol Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a CPU-validated, outcome-independent Stonehenge Active Runtime Pilot V3 protocol without executing Pilot data collection.

**Architecture:** A task-local JSON protocol binds the exact PR #141 evidence, development-exposed cohort, V3 geometry, map, execution form, required evidence, and predeclared decisions. A task-local validator verifies those artifacts, their hashes, zero execution counts, and a zero protected-source diff before the protocol commit.

**Tech Stack:** Git, Python 3 standard library, JSON, SHA-256, Markdown.

---

### Task 1: Lock the exact upstream evidence

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_INPUT_LOCK.json`

- [ ] Verify PR #141 is an Open Draft at `aeab949629d314e930fda6c65bcc68c724fbf6c6`.
- [ ] Hash the frozen Smoke V3 protocol, locks, summary, validation, V3 geometry policy, and V3 validation result.
- [ ] Record the protocol SHA-256 and all zero execution counters in the input lock.

### Task 2: Freeze the prospective Pilot protocol

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_PROTOCOL.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_DECISION_RULES.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_DEVELOPMENT_EXPOSURE.json`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_REQUIRED_EVIDENCE_SCHEMA.json`

- [ ] Freeze trial IDs `[5,15,25,35,45,55,65,75,85,95]`, order, seed 0, 500-cycle cap, serial execution, separate processes, GPU 1, and the official environment.
- [ ] Freeze hard geometry `0.015/0/0.015/0 q` and the `0.025 q` diagnostic shell with every runtime authority flag false.
- [ ] Freeze integrity hard blocks, method-level diagnostic blocks, legal fallback interpretation, and the sole advance rule before outcomes exist.
- [ ] Mark all ten trials development-exposed and prohibit their unlabelled reuse in a V3 primary confirmatory cohort.
- [ ] Freeze all required trial and aggregate evidence fields without creating a runner or execution output.

### Task 3: Implement CPU-only validation

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/validate_active_runtime_pilot_v3_protocol.py`
- Create: `reproduction/pilot/active_runtime_pilot_v3/PILOT_V3_PROTOCOL_VALIDATION.json`

- [ ] Parse every task-local JSON file and verify exact values and required fields.
- [ ] Verify upstream artifact hashes and the independent Pilot protocol hash.
- [ ] Verify the exact upstream commit is an ancestor and every worktree change stays inside the task directory.
- [ ] Verify GPU Pilot, Official100, oracle, Formal, and reference-arm counts are all zero.
- [ ] Run `python -m py_compile reproduction/pilot/active_runtime_pilot_v3/validate_active_runtime_pilot_v3_protocol.py` and expect exit code 0.
- [ ] Run `python reproduction/pilot/active_runtime_pilot_v3/validate_active_runtime_pilot_v3_protocol.py --repo-root . --phase protocol` and expect `PASS_ACTIVE_RUNTIME_PILOT_V3_PROTOCOL_VALIDATION` plus five zero counters.

### Task 4: Freeze documentation and Git evidence

**Files:**
- Create: `reproduction/pilot/active_runtime_pilot_v3/README.md`
- Create: `reproduction/pilot/active_runtime_pilot_v3/DRAFT_PR_BODY.md`
- Create: `reproduction/pilot/active_runtime_pilot_v3/downstream_handoff.json`

- [ ] Run `git diff --check` and verify no path outside `reproduction/pilot/active_runtime_pilot_v3/` changed relative to `aeab949629d314e930fda6c65bcc68c724fbf6c6`.
- [ ] Commit the frozen protocol as `Freeze Active Runtime Pilot V3 protocol` before any Pilot outcome exists.
- [ ] Record the exact protocol commit in the Draft PR body without changing the frozen protocol.
- [ ] Push `freeze-active-runtime-pilot-v3-protocol-v1` and create an Open Draft PR based on `freeze-active-runtime-smoke-v3-protocol-v1`.

### Self-review

- [ ] Confirm every attachment requirement maps to one artifact or validator check.
- [ ] Confirm the plan contains no runtime execution step and no parameter-selection path.
- [ ] Confirm all new files are task-local and no shared runtime or prior evidence is modified.
