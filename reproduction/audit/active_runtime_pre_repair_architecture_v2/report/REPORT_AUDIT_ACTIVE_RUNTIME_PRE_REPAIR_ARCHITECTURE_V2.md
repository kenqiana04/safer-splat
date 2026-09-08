# REPORT — AUDIT_ACTIVE_RUNTIME_PRE_REPAIR_ARCHITECTURE_V2

## Answer-first findings

1. **Upstream and scope.** PR #123 exact head `3b01171d7d25c7f81efd53d0486ab95d7c73c7a9` is preserved. All A–Q domains completed; no runtime/production mutation and no real execution occurred.
2. **Primary confirmed defects.** The coordinator computes alternative permission from `backup_valid && deadline.status == OPEN` at lines 376/393/410, branches on deadline at 416, and suppresses a certified candidate at 442–443. This is the frozen PR123 policy leak. The runtime transition carrier omits frozen row metadata and derives semantic flags from destination. Stage exceptions route and then unconditionally return `_blocked_result`; alternative provider statuses can collapse to an empty inventory.
3. **Latent risks.** Terminal evaluation is passed `fallback_context=True`; backup lifecycle is projected to a boolean; UNKNOWN reason scope is heuristic; BYPASS AST identity is non-portable despite source/body preservation; trace-fault behavior lacks dynamic pre-repair coverage.
4. **What is verified.** `Supervisor.arbitrate` remains the static final selector, `PlantCommitAdapter` remains the sole plant owner, ActiveRunner/token/trace files are unchanged, R0 is diagnostic-only, legacy 0.11 leakage and oracle feedback edges are absent, and no unauthorized numeric replacement was found. Existing CPU regression history is recorded accurately (110 tests, 109 pass, 1 source-equal/AST-hash failure).
5. **Interpretation boundary.** The audit is complete even though the implementation is defective. It does not turn PR123's blocked conformance into PASS and does not add scientific data.

## Domains A–Q

The domain manifest marks all 17 domains `COMPLETE`; each output records evidence, findings, and any dynamic limitation without using an early-stop status. Transition fidelity covers all 43 unique frozen rows. The symbolic checker enumerates independent counterexamples, and 48 adversarial probes complete after earlier findings.

## Repair DAG

R1 `REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2` addresses D-AUTH-001 and D-TRANS-001. R2 `REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2` addresses D-EXC-001 and D-ALT-001 after R1. R3 is the existing conformance revalidation. No repair, smoke, ACTIVE rollout, GPU, oracle, or official100 is authorized by this audit.

## Decision

`FINAL_STATUS=PASS_FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2` (audit completeness only).

`FINAL_DECISION=FREEZE_FULL_PRE_REPAIR_FINDINGS_AND_ADVANCE_BOUNDED_REPAIR_DAG`.

Only next task: `REPAIR_ACTIVE_RUNTIME_AUTHORITY_AND_ROUTING_BOUNDARY_V2`.
