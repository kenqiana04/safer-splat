# Report: Freeze Terminal / External Emergency Policy V2

## Decision first

`FINAL_STATUS=PASS_TERMINAL_EMERGENCY_POLICY_V2_FREEZE`

`FINAL_DECISION=FREEZE_TERMINAL_EMERGENCY_POLICY_AND_ADVANCE_BLOCKER_DAG`

Only next task: `FREEZE_INDEPENDENT_EVALUATION_ORACLE_V2`.

The policy is statically closed without implementing a runtime terminal or emergency controller. Membership, certification, eligibility, selection/commit, and the outside-method boundary are distinct.

## Terminal semantics

`TERMINAL_SET_MEMBER` is a state predicate only. It has no action, goal, emergency, selection, or commit authority. A zero-velocity initial state therefore cannot preempt timely certified navigation.

The legacy source supports one parameterized certificate primitive: `TERMINAL_ZERO_HOLD=(0,0,0)`. It is admissible under `NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2`, but becomes method-certified only with exact current state/time, map, geometry, actuator, dynamics/timebase, current/segment zero-hold evidence, deadline preparation identity, and the frozen assumption set.

`TERMINAL_CERTIFICATE_READY` is evidence, not eligibility or authority. Eligibility additionally requires a current Supervisor context. `TCTX_GOAL_HOLD` is defined but its runtime goal-completion authority remains unresolved. `TCTX_FALLBACK_NO_NAV_NO_VALID_BACKUP` is policy-frozen. External requests may query an already-certified terminal action but cannot certify one.

## Arbitration and backup interaction

The unchanged priority is:

1. timely certified navigation with a prepared next-cycle token;
2. still-valid retained backup;
3. current certified terminal action in an eligible context;
4. `ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION`.

`BACKUP_TOKEN_EXHAUSTED != TERMINAL_ACTION_AUTHORIZED`. A terminal reference from a backup bundle must be revalidated against certificate hash, state/time, map, geometry, actuator, dynamics/timebase, exact action, deadline, and current context. A stale reference cannot commit.

## Deadline and external boundary

Deadline verdict is `COMPATIBLE_WITHOUT_LOGIC_CHANGE`. OPEN permits bounded evaluation, WARNING forbids new high-cost terminal work, and EXPIRED forbids new certification/search. An action already ready before the guard may remain selectable while all identities remain valid. Expiry never creates safety.

External emergency authority is `UNRESOLVED_OUTSIDE_METHOD`. When the method has no certified executable action, it returns the assurance boundary and its theorem ends. Zero control, hold-last, nominal/desired control, arbitrary braking, solver failure, return, break, or process termination are not method-certified emergency actions.

## Fail-close and claim boundary

`SOFTWARE_FAIL_CLOSE != PHYSICAL_SAFE_STOP`. Software refusal cannot be counted as safe stop, collision avoided, or terminal success without an independent execution oracle. Terminal safety also differs from navigation progress and task success.

This task supports only static policy consistency. It does not support collision reduction, real-world safety, physical safe stop, recursive safety under hardware uncertainty, real-time guarantees, or deployment readiness.

## Validation

- PR #112 exact identity: PASS.
- Frozen PR #107–#112 artifacts: unchanged.
- TP-01–TP-24: complete.
- PTP-01–PTP-20: 20/20 PASS.
- Adversarial scenarios: 24/24 PASS.
- Counterexamples: 0.
- Explicit reachable abstract states: 18; Cartesian-product generation: 0.
- Unit tests: 12/12 PASS.
- Validator: `PASS_TERMINAL_EMERGENCY_POLICY_V2_VALIDATION`.
- Production/runtime diff: 0.

## Remaining blocker

`INDEPENDENT_EVALUATION_ORACLE` remains unresolved. The V5 DAG mechanically selects `FREEZE_INDEPENDENT_EVALUATION_ORACLE_V2`; runtime implementation remains blocked.
