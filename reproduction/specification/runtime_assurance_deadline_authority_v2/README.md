# Runtime Assurance Deadline Authority V2

This directory freezes a design-only deadline authority contract for the SAFER-Splat V2 runtime-assurance chain. It adds no runtime hook, controller path, solver behavior, rollout, benchmark, or numerical deadline.

The sole global deadline owner is `SUPERVISOR`. Certificate layers report typed results and local timeouts; they do not select timing policy. Expiry means that the current cycle cannot start or continue uncertified search. It does not mean collision, unsafe state, or controller failure.

Canonical artifacts:

- `RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json`: authority, states, legal post-expiry choices, and non-claims.
- `RUNTIME_DECISION_TIMELINE_V2.json`: ordered stage and timestamp contract.
- `DEADLINE_STATE_TRANSITION_TABLE_V2.csv`: complete state/action rules.
- `DEADLINE_AUTHORITY_INVARIANTS_V2.json`: machine-checkable invariants.
- `CROSS_LAYER_DEADLINE_CONSISTENCY_V2.csv`: layer ownership audit.
- `contract_rules.py`: task-local static checker used only by tests.

Numeric cycle budgets, warning reserve, latest-safe commit point, and clock identity remain implementation prerequisites. Missing values produce `GLOBAL_DEADLINE_UNKNOWN`; no default is authorized.
