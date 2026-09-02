# Terminal and Deadline Interaction V2

Deadline pressure does not supply a terminal certificate. A terminal action is executable only when its complete frozen status is `CERTIFIED_TERMINAL_READY` before the relevant deadline boundary and its geometry, actuator, state, map, and temporal identities remain valid at Supervisor commit.

`DEADLINE_WARNING` prohibits starting a new terminal search. `DEADLINE_EXPIRED` prohibits constructing or certifying a terminal action. Expiry is never an emergency shortcut and never implies that stopping, zero control, or another terminal command is safe. If no already certified legal action exists, control leaves the method through the explicit outside-method boundary.
