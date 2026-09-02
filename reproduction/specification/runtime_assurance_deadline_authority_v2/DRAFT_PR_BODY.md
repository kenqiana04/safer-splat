## Purpose

Freeze the V2 runtime-assurance deadline authority as a specification-only safety decision boundary. This PR is based exactly on Draft PR #109 head `729b3c78a81f2f3ca8948916b64dcb6e2c50fc66` and preserves PRs #107–#109 read-only.

## Frozen contract

- The Supervisor is the only global deadline owner.
- Every cycle stage has a start timestamp, end timestamp, and bounded budget.
- `DEADLINE_OPEN`, `DEADLINE_WARNING`, and `DEADLINE_EXPIRED` have explicit transitions.
- Warning forbids new high-cost search. Expiry is absorbing and forbids new candidate, alternative, backup, and terminal search.
- Post-expiry arbitration is limited to already certified navigation, an already valid backup, an already certified terminal action, or the outside-method boundary.
- Backup validity binds geometry, actuator, state, map, and temporal identity before expiry.
- Terminal execution requires `CERTIFIED_TERMINAL_READY`; expiry is not automatic safety.
- `GLOBAL_DEADLINE_UNKNOWN` and `LOCAL_CERTIFICATE_TIMEOUT` are separate non-success results.

## Validation

- 10/10 static contract tests pass.
- `PASS_RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2_VALIDATION`.
- Protected and production source mutation count: 0.
- Runtime, rollout, GPU, collection, benchmark, and tuning counts: 0.

## Evidence boundary

No numerical budget, real-time guarantee, hardware latency guarantee, computational superiority, collision reduction, or deployment readiness is claimed. Alternative-source, terminal/emergency, backup-token, and independent-oracle blockers remain unresolved.

`FINAL_STATUS=PASS_RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2_FREEZE`

`FINAL_DECISION=FREEZE_RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_ALTERNATIVE_SOURCE_AUTHORITY_V2`.
