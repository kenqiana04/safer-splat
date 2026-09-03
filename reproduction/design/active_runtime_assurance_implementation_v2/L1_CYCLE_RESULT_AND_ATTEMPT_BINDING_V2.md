# L1 Cycle Result and Attempt Binding V2

For the position-first forward-Euler double integrator, the closed immediate segment `Segment(p_k,p_k1)` is candidate-independent. `L1Runtime.evaluate_cycle` computes it exactly once per cycle with the frozen state, dt, map snapshot, G3 geometry identity, and PR #108 effective radius.

The result is immutable `L1CycleResult(cycle_l1_result_id, cycle_id, state_id, segment_id, map_id, geometry_id, status, reason, evidence_hash)`. Every primary or alternative attempt receives a fresh `L1AttemptBinding(attempt_id, candidate_id, cycle_l1_result_id, state_id, segment_id, binding_hash)`. Reusing the cycle computation is allowed; reusing another candidate's attempt identity is forbidden. A mismatch or missing binding becomes typed UNKNOWN and cannot pass.
