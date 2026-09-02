# Runtime Assurance Supervisor V2

The supervisor is the only component with action-selection and plant-commit authority.

Per active cycle it retains a still-valid old backup, receives one primary proposal, and runs C0 → L2 → L3 before the latest-safe commit guard. A new navigation action is committed only when all three pass and a next-cycle witness/token is ready. Old backup replacement is atomic at commit.

Candidate-local C0/L2/L3 failures or local-compute UNKNOWN may enter bounded L4 only when the retained fallback is valid, deadline is open, budget remains, and the alternative source is lawful. Every alternative restarts C0 → L2 → L3. Global authority/evidence UNKNOWN never enters L4 merely by changing candidate.

Deterministic arbitration priority is:

1. timely certified navigation with prepared new token;
2. still-valid retained backup;
3. certified terminal action in an eligible fallback/goal context;
4. `ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION` with external emergency authority explicitly outside the theorem.

The guard preempts search. At or after guard there is no new certification attempt: the supervisor uses evidence prepared before the guard or selects the explicit boundary. A solver failure, break, string, or missing result is never a physical safe-stop proof.

Active mode certifies proposals before commit. Shadow mode observes `SELECTED_EXECUTED_CONTROL` only after commit and has no return channel, candidate authority, fallback authority, terminal authority, or commit authority.
