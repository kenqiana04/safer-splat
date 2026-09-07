
# Public cycle integration gap diagnosis V2

## Frozen evidence

PR #120 is retained unchanged as an Open Draft at the exact head recorded in
`PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json`. Its final status is
`BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`; 43/43 transition
assertions are present, but 35 critical public routes and all 6 genuine E2E
scenarios are blocked. No runtime or production file is changed by this task.

## What already exists

The frozen runtime contains `AuthorityRegistry`, `StartAdmission`,
`DiagnosticR0`, `L1Runtime`, `PrimaryProposalAdapter`, `C0Admission`,
`L2Runtime`, `L3Runtime`, `AlternativeProvider`, `BackupTokenStore`,
`TerminalRuntime`, `DeadlineTracker`, `Supervisor`, `PlantCommitAdapter`,
`TraceWriter`, and `ActiveRunner`.

## Exact missing seam

There is no runtime-owned public API that performs trial admission, R0
diagnostic handoff, phase sequencing, typed result handoff, deadline-stage
admission, transition lookup, fallback entry, backup validation, terminal
timing, final arbitration, commit invocation, and cycle-result construction.
`ActiveRunner.commit_active_decision(...)` consumes a precomputed
`SupervisorDecision`; it is not a cycle coordinator. `Supervisor.certify_candidate(...)`
consumes precomputed L1/binding/C0/L2/L3 data. `Supervisor.arbitrate(...)`
consumes precomputed candidate/L3/backup/terminal/deadline data and remains the
sole selection owner.

## Frozen root cause

`MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION` (CE-001). The repair is a future
composition design, not a correction to PR #120 and not a second safety policy.
