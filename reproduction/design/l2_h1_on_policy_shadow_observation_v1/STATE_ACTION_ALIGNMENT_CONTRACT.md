# State/Action Alignment Contract

The atomic observation unit is one accepted frozen-controller decision. The immutable key tuple is:

`(run_id, trial_id, step_id, state_sequence_id, decision_commit_id, candidate_group_id, selected_candidate_id, map_snapshot_ref)`.

Capture order is fixed:

1. freeze pre-plant `x_k` and derive `p_k=x_k[:3]`, `v_k=x_k[3:]`;
2. freeze runtime `dt` and accepted selected `u_k` after the success guard;
3. assign `decision_commit_id` exactly once;
4. hash canonical state, candidate group, selected control, and map reference;
5. enqueue the immutable payload without waiting;
6. only then allow the pre-existing plant update to use the same `u_k`.

The worker must compute:

`p_k1 = p_k + dt*v_k`

`p_k2 = p_k + 2*dt*v_k + dt^2*u_k`

It must never substitute the logged post-update `x_(k+1)` for `x_k`.

## Required anti-off-by-one checks

1. **Commit uniqueness:** one and only one payload per `decision_commit_id`; IDs are monotonic within trial.
2. **State hash:** recompute `state_hash` from captured `p_k/v_k/dt/state_sequence_id` canonical bytes.
3. **Control hash:** recompute `u_k_hash` and require it equals the selected native-candidate hash.
4. **Plant trace join:** where deterministic trace QA is available, `x_(k+1)` must equal the frozen plant transition of captured `x_k/u_k/dt` within the pre-frozen equivalence tolerance; it must not equal the payload's `x_k` key by accidental index shift.
5. **H1 recomputation:** independently recompute `p_k1/p_k2/H1_segment_hash` from captured fields and require exact canonical-hash equality.
6. **Timestamp relation:** `control_timestamp/logical_index` and `step_id` must be one-to-one; no result may join to a later state sequence.
7. **Candidate join:** `selected_candidate_committed=true` and exactly one native candidate has `selected_for_execution=true`.
8. **Map join:** payload and result must use the same `map_snapshot_ref`, resolved by the frozen run map manifest.

Any failure is `OBSERVATION_INCOMPLETE`, excluded from the evaluable endpoint but included in logging denominators. It is never converted to L2 UNKNOWN.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
