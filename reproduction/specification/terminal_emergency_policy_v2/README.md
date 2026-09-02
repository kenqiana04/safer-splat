# Terminal / External Emergency Policy V2

This directory freezes policy-only arbitration semantics on exact PR #112. It does not implement a terminal controller, emergency controller, runtime supervisor, backup token, or plant integration.

The contract separates five objects:

1. `TERMINAL_SET_MEMBER`: state predicate only.
2. `TERMINAL_CERTIFICATE_READY`: complete evidence for one exact state/action/authority tuple.
3. `TERMINAL_ACTION_ELIGIBLE`: Supervisor context admits that already-certified action to arbitration.
4. `TERMINAL_ACTION_SELECTED` / `COMMITTED`: Supervisor selection followed by exact identity-preserving plant commit.
5. `EXTERNAL_EMERGENCY_BOUNDARY`: no method-certified executable action exists; the theorem ends.

Frozen priority is `CERTIFIED_NAVIGATION > VALID_RETAINED_BACKUP > ELIGIBLE_CERTIFIED_TERMINAL > ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION`. External emergency authority remains unresolved and outside the method.

No runtime, GPU, rollout, pilot, benchmark, formal collection, tuning, collision-efficacy analysis, or V1 reinterpretation was authorized or performed.
