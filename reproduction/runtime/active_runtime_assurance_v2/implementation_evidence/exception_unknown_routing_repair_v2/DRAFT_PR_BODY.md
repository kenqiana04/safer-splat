## Summary

Closes the two PR #124 R2 defects on top of exact PR #125 head `303aa01c08e82d1d77a5f5cabf5127344109a996`:

- D-EXC-001: typed stage exceptions now follow Supervisor-resolved destinations instead of an unconditional Coordinator block.
- D-ALT-001: provider availability, finite absence, invalid source, missing provenance, and unresolved status remain distinct.
- Replaces substring reason-scope inference with exact typed mappings and `UNRESOLVED_SCOPE` fallback.

## Evidence

- 133 CPU tests PASS
- 34 bounded R2 probes PASS
- actual-runtime model check: 0 counterexamples
- validator: `PASS_R2_ACTIVE_RUNTIME_EXCEPTION_UNKNOWN_ROUTING_V2_VALIDATION`
- PR #107 transition rows and PR #125 R1 authority repair unchanged
- BYPASS_REVALIDATION_REQUIRED=false
- real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS counts all zero

## Decision boundary

`FINAL_STATUS=PASS_REPAIR_ACTIVE_RUNTIME_EXCEPTION_AND_UNKNOWN_ROUTING_V2`

`FINAL_DECISION=FREEZE_R2_EXCEPTION_UNKNOWN_REPAIR_AND_ADVANCE_FULL_RECONFORMANCE`

Only next task: `REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2`. Smoke is not authorized by this PR.
