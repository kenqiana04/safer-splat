# Active Runtime Contract Reconformance V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently revalidate PR #122's public Active runtime composition against the frozen PR #107–#121 contracts without changing runtime or executing real trials.

**Architecture:** A task-local CPU harness imports the exact PR #122 runtime, records calls at module seams, and compares every frozen transition row and public-cycle outcome with its source authority. The harness freezes the first critical counterexample and stops later dynamic scenarios; static ownership, identity, and mutation checks still complete.

**Tech Stack:** Python 3.11, `unittest`, `ast`, immutable runtime dataclasses, CSV/JSON evidence, Git/GitHub CLI.

## Execution outcome

- Harness and execution locks were frozen before substantive checks.
- PR #120's missing public composition root was structurally confirmed closed.
- `RC-POLICY-01` was frozen as the first critical counterexample: the coordinator interprets deadline/search/navigation eligibility before Supervisor routing/arbitration.
- All later dynamic scenarios, six genuine E2E cases, and full 43-rule dynamic coverage were intentionally not executed.
- Static audits, model check, validator, report, and downstream handoff were completed without runtime correction.

---

### Task 1: Freeze inputs and upstream identity

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/ACTIVE_RECONFORMANCE_INPUT_LOCK.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/build_reconformance_harness_v2.py`

- [ ] Verify PR #122 remains an Open Draft at `bdc8273295d30cbeef029a38ed80153c5cc1d24d` with base `4148e671128444d357ea33f6e5c15d0dd2928411`.
- [ ] Hash PR #107–#122 authorities, runtime files, BYPASS evidence, PR #120 blocker evidence, and PR #122 implementation evidence.
- [ ] Record `runtime_correction_quota=0` and all real-execution counters as zero.
- [ ] Run the lock builder and verify every referenced path exists and hashes deterministically.

### Task 2: Build fail-closed conformance harness

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/tests/reconformance_support.py`
- Create: the twenty required `tests/test_*_reconformance.py` modules from the protocol.
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/scenario_manifest.json`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/EXPECTED_TRANSITION_RECONFORMANCE_MATRIX_V2.csv`

- [ ] Reuse the actual `ActiveCycleCoordinator`, `Supervisor`, `TransitionTable`, `ActiveRunner`, token store, terminal runtime, deadline tracker, and trace writer with CPU-only injected backends.
- [ ] Instrument module call order without precomputing L1, candidates, certificates, or Supervisor decisions.
- [ ] Add static AST ownership and policy-leak classification checks.
- [ ] Add raw 43-row field-by-field fidelity and exact-one lookup checks.
- [ ] Add public start/L1/P0/C0/L2/L3, exception, deadline, alternative, backup, terminal, commit, trace, and genuine E2E tests.
- [ ] Make the first critical mismatch write `FIRST_COUNTEREXAMPLE_V2.json`; do not change runtime.

### Task 3: Freeze execution authority

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/freeze_reconformance_execution_lock_v2.py`
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json`

- [ ] Hash the input lock, scenario manifest, expected 43-row matrix, fixtures, all test source, model checker, and validator.
- [ ] Set substantive-execution state to locked and correction quota to zero.
- [ ] Commit the harness as `validation(reproduction): freeze active runtime reconformance harness V2`.

### Task 4: Execute targeted CPU conformance

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/model_check_active_public_cycle_reconformance_v2.py`
- Create: task-local audit JSON/CSV outputs and scenario results.

- [ ] Run identity and PR #120 blocker-closure checks first.
- [ ] Run raw transition fidelity and exact-one checks before broad dynamic scenarios.
- [ ] If a critical counterexample appears, freeze it immediately and skip later dynamic scenarios while completing static validator checks.
- [ ] Otherwise run all public-cycle scenarios, six genuine E2E cases, 43-rule critical dynamic coverage, PR #122's 110-test regression, and the actual model checker.
- [ ] Confirm no runtime, production, GPU, smoke, oracle, official100, or real BYPASS execution occurred.

### Task 5: Validate, report, and publish evidence

**Files:**
- Create: `reproduction/validation/revalidate_active_runtime_contract_conformance_v2/validate_revalidated_active_runtime_contract_conformance_v2.py`
- Create: `validation_result.json`, reviewer, decision, handoff, Draft PR body, and report files required by the protocol.

- [ ] Run the validator's 42 checks and preserve the observed PASS or mechanical BLOCK status.
- [ ] Verify `git diff --check`, runtime diff zero, production diff zero, and exact staged paths.
- [ ] Commit evidence as `validation(reproduction): freeze revalidated active contract evidence V2`.
- [ ] Push `revalidate-active-runtime-contract-conformance-v2` and create one Open Draft PR against `implement-active-runtime-public-cycle-composition-v2`.
- [ ] Stop without smoke or any downstream task.

### Self-review

- [ ] No runtime or upstream artifact is modified.
- [ ] The first critical counterexample protocol is fail-closed and deterministic.
- [ ] PASS is impossible unless all required dynamic and static gates pass.
- [ ] BLOCK never triggers a runtime or contract correction.
- [ ] Only the mechanically selected downstream task is reported.
