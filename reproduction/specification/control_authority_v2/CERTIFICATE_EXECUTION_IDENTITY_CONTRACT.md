# Certificate/Execution Identity Contract

## Current frozen simulation observation

For a successful Clarabel solve, the CBF feasibility constraints are solved for the vector returned as `u_out`. `run.py` assigns that vector to `u`, checks solver success, and passes the same vector to the simulated dynamics. No value-changing operation occurs between solver return and plant update.

Thus the current successful simulation path has `certificate_input_control == selected_control == executed_control`. This statement is bounded to the simulated source path and does not establish actuator feasibility, physical tracking, or deployment readiness.

## Target V2 contract

A certificate record must bind:

- `candidate_id`
- canonical control-vector hash
- solver-validity identity
- actuator-admission identity
- applicable L0–L5 certificate identities
- selected-control identity
- committed execution identity

The selected and committed vector/hash must match byte-for-byte under the frozen numeric serialization. If any mapping changes the vector, the prior certificate does not apply: the mapped value receives a new candidate identity and must be re-certified before commitment.

Solver failure, unknown actuator authority, hidden transformation, or identity mismatch produces no committed control under this contract.
