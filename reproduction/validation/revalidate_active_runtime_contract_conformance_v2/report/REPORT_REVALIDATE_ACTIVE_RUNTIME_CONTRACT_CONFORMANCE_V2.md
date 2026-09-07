# Report: Revalidate Active Runtime Contract Conformance V2

## Answer first

`FINAL_STATUS=BLOCKED_ACTIVE_RECONFORMANCE_BY_COORDINATOR_POLICY_LEAK`

`FINAL_DECISION=DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; FREEZE_FIRST_COUNTEREXAMPLE_AND_DIAGNOSE_COORDINATOR_POLICY_BOUNDARY`

PR #120's missing public composition root is structurally closed: `ActiveCycleCoordinator.start_trial`, `run_cycle`, and `finalize_trial` exist and invoke the frozen modules, Supervisor, and ActiveRunner. Full contract conformance is nevertheless blocked.

The first critical counterexample is `RC-POLICY-01`. In `active_cycle.py`, the coordinator computes alternative permission from backup validity and `DEADLINE_OPEN` (lines 376, 393, 410), selects a deadline-guard path (line 416), and filters the certified navigation candidate by its own deadline interpretation (lines 442–443). Frozen PR #121 assigns deadline interpretation and alternative permission to Supervisor. This is a policy/authority leak, not mechanical event conversion.

## Consequences

- Runtime correction quota remained zero; no source or contract was changed.
- All later dynamic scenarios stopped immediately after the first critical mismatch.
- Genuine E2E reconformance is therefore `0/6`, and critical dynamic coverage is `0%`; these are **not** failed scientific trials.
- No smoke, real ACTIVE rollout, GPU work, scientific oracle, official100, or real BYPASS pair ran.
- BYPASS source identities remain preserved and no BYPASS revalidation is currently required.

## Secondary static observation

The 43-row audit also found that runtime `TransitionRule` and `RoutingDecision` do not carry all frozen row-level metadata (`action_authority`, backup retention/creation, and theorem interpretation; `TransitionRule` also lacks explicit search/arbitration permissions). This was recorded after the dynamic stop only as static evidence and is not substituted for the first counterexample.

## Remaining blocker and handoff

The next bounded task is `DIAGNOSE_ACTIVE_CYCLE_COORDINATOR_POLICY_LEAK_V2`. It must diagnose the minimal ownership correction without performing runtime changes, smoke, or real execution in this reconformance task.
