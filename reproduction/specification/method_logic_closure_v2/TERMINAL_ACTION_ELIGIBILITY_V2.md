# Terminal action eligibility V2

`TERMINAL_SET_MEMBER` is a state predicate. `TERMINAL_ACTION_ELIGIBLE` additionally requires a certified executable terminal action under current map, geometry, actuator, temporal, and zero-hold contracts plus an eligible supervisor context.

Membership never preempts normal navigation. Deterministic priority is certified navigation, valid retained backup, certified terminal action, then assurance boundary. A terminal action is eligible when the goal/task explicitly allows hold, or when no timely new navigation action and no valid retained backup exist and the terminal action itself is certified. An emergency fallback context may also authorize evaluation, but the emergency policy remains a separate preimplementation contract.

Zero velocity or terminal-set membership alone is insufficient. A program break, no-result record, solver failure, or string labelled fail-close has no execution certificate.
