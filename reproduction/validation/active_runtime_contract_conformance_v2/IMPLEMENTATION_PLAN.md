# Plan: Validate Active Runtime Contract Conformance V2

> **For agentic workers:** REQUIRED SUB-SKILL: Use `writing-plans` to execute this plan task-by-task.

**Goal:** Validate PR #116 ACTIVE_RUNTIME_ON against the frozen PR #107–#115 contracts and PR #119 evidence without modifying production runtime or running GPU/real ACTIVE experiments.

**Architecture:** Use the PR #119 runtime checkout as an immutable source-under-test, record exact upstream/blob identities, audit public entrypoints and authority ownership, exercise only CPU deterministic public APIs with test doubles limited to numerical backends/clock/witnesses, and fail closed on the first integration or contract counterexample.

**Tech Stack:** Git/GitHub identity checks, Python 3, unittest/pytest-compatible CPU fixtures, JSON/CSV artifacts, static source audit, model-check script, task-local validator.

## Task 1: Freeze upstream identities and task boundaries

- [ ] Verify PR #119 state/title/branch/head/base and prior BYPASS PASS evidence.
- [ ] Record PR #107–#119 contract/artifact identities and PR #116 runtime blob hashes.
- [ ] Write `ACTIVE_CONFORMANCE_INPUT_LOCK.json` and protected-source diff baseline.
- [ ] Create the scenario manifest and explicit zero-runtime counters.

## Task 2: Audit the public ACTIVE integration and ownership seams

- [ ] Inspect PR #116 public entrypoints, composition root, transition usage, Supervisor routing, PlantCommit, token, terminal, deadline, and trace paths.
- [ ] Write `ACTIVE_RUNTIME_PUBLIC_INTEGRATION_AUDIT_V2.md` and authority ownership JSON.
- [ ] Build the 43-rule matrix and canonical call-order/fixture-boundary artifacts.
- [ ] Record any integration orchestration gap as a first counterexample without patching runtime.

## Task 3: Build the locked CPU-only conformance harness

- [ ] Add only task-local deterministic fixtures and tests; do not replace Supervisor, commit, token, terminal, C0, or trace semantics.
- [ ] Add UNKNOWN routing, trace/oracle, scenario result, model-check, and validation scripts.
- [ ] Generate the execution lock before running the suite, hashing the manifest/matrix/tests/validator/model-checker and source identities.

## Task 4: Run bounded validation and fail closed

- [ ] Run static checks and CPU targeted tests only.
- [ ] Stop unnecessary scenarios after the first genuine integration/contract counterexample.
- [ ] Preserve first counterexample and classify unexecuted scenarios as blocked rather than fabricating PASS.

## Task 5: Freeze evidence and handoff

- [ ] Run the task-local validator and reviewer against the frozen evidence.
- [ ] Write final decision, downstream handoff, report, and Draft PR body with all zero-runtime counters.
- [ ] Confirm production/runtime/protected diff is zero and stage only this task directory.
- [ ] Commit, push, and create the Draft PR; do not run any next smoke or real ACTIVE task.
