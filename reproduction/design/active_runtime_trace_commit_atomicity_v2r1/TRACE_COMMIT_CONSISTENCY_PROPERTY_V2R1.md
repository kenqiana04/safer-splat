# Trace/commit consistency property V2R1

Every authorized commit attempt terminates in exactly one typed class:

1. **No confirmed plant commit:** no executed-action claim is emitted; the result is `ABORTED_BEFORE_PLANT` or `PLANT_NOT_COMMITTED`.
2. **Confirmed plant commit:** the execution fact and receipt are retained, and evidence is either `COMPLETE`, `COMMITTED_TOKEN_INCOMPLETE`, or `COMMITTED_TRACE_INCOMPLETE`.
3. **Unresolved plant outcome:** the result is `PLANT_OUTCOME_UNRESOLVED` with `RECOVERY_REQUIRED`.

`CommitTransactionResult` is an immutable additive runtime fact with: attempt identity, plant outcome tri-state, committed tri-state, optional receipt, token status, trace status, evidence status, optional post-state, recovery-required flag, retry-allowed flag, failure reason, and software-transaction state. It is not a scientific outcome.

The evidence-status domain is: `COMPLETE`, `NO_ACTION_COMPLETE`, `ABORTED_BEFORE_PLANT`, `PLANT_NOT_COMMITTED`, `PLANT_OUTCOME_UNRESOLVED`, `COMMITTED_TOKEN_INCOMPLETE`, `COMMITTED_TRACE_INCOMPLETE`, `NO_ACTION_TRACE_INCOMPLETE`, `FINALIZATION_INCOMPLETE`, and `RECOVERY_REQUIRED`.

An incomplete or unresolved transaction never transitions directly to `READY`; automatic retry and automatic plant replay are forbidden; physical rollback is never fabricated; and a required incomplete trace is never oracle-eligible.
