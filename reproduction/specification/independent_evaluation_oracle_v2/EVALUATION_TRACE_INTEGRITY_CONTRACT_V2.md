# Evaluation Trace Integrity Contract V2

The future oracle consumes only a content-addressed, immutable trace locked before evaluation. Every committed transition binds `x_k`, selected and executed action identities/vectors, action role, and exact `x_(k+1)` under one cycle index. Trial, map, geometry, actuator, dynamics/timebase, deadline, terminal-policy, and oracle identities are mandatory.

The oracle rejects missing committed transitions, sequence gaps, nonfinite states, hash mismatches, mutable references, or a selected/executed mismatch without an explicit actuator-authority explanation. Missing timing may make timing UNKNOWN without necessarily invalidating geometry, but missing state/action geometry makes the affected outcome `EVAL_UNKNOWN`; it is never silently SAFE.
