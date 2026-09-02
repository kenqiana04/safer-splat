# Terminal Arbitration Priority V2

The Supervisor remains the sole arbitration and commit authority. Priority is unchanged from PR #107:

1. timely certified navigation with a complete prepared next-cycle token;
2. still-valid retained backup;
3. current certified terminal action in an eligible context;
4. `ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION`.

Thus `NAVIGATION > TERMINAL`, even when `TERMINAL_SET_MEMBER=true`; and `VALID_BACKUP > TERMINAL`, even when zero-hold is simpler. Terminal is above the boundary only when certificate, action, state/time, map, geometry, actuator, dynamics/timebase, deadline preparation, and context identities all remain valid.

No certificate layer selects or commits an action. `TERMINAL_CERTIFICATE_READY != TERMINAL_ACTION_ELIGIBLE != TERMINAL_ACTION_SELECTED != TERMINAL_ACTION_COMMITTED`.
