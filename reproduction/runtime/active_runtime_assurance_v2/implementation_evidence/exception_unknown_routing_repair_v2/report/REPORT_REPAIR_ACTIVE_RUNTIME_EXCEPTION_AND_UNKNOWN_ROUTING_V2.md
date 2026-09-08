# REPORT_REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2

## Answer first

- D-EXC-001: CLOSED. Exceptions at L1, proposal, C0, L2, L3, alternative provider, terminal, and arbitration produce typed evidence. Every resolved route is executed by the shared destination loop; unresolved arbitration failure blocks with no action.
- D-ALT-001: CLOSED. `ALT_AVAILABLE`, `NO_ALTERNATIVE_AVAILABLE`, `SOURCE_INVALID`, and `PROVENANCE_MISSING` remain distinct; unexpected values become `UNRESOLVED_STATUS`.
- Reason scope: exact reason-code mapping only. Arbitrary text containing missing/timeout/exception remains `UNRESOLVED_SCOPE`.
- Fallbacks: retained backup and eligible terminal remain reachable when Supervisor authority permits. No fallback yields the assurance boundary with zero plant commit.
- Preservation: R1 authority and 43-row metadata, `Supervisor.arbitrate`, ActiveRunner, PlantCommit, token, terminal, trace, provider, and BYPASS semantics are unchanged.

## Verification

- CPU tests: 133/133 PASS.
- Bounded adversarial probes: 34/34 PASS.
- Actual-runtime model check: 0 counterexamples.
- Validator: PASS_R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_V2_VALIDATION (47/47 checks).
- Real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS: 0/0/0/0/0/0.

## Decision

FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2

FINAL_DECISION=FREEZE_R2_EXCEPTION_UNKNOWN_REPAIR_AND_ADVANCE_FULL_RECONFORMANCE

Remaining blockers: full Active Runtime contract reconformance remains required; smoke is not authorized.

Only next task: REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2
