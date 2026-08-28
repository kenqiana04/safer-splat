# Report: Implement L2/H1 on-policy shadow instrumentation V1

## Direct answers

**Q1. Does PR #96 identity match exactly?** YES. Open Draft, `design-l2-h1-on-policy-shadow-observation-v1`, `1783aff5f6d221efc26d34f8b47b966e2d9eee3e`, base `l2-h1-shadow-frozen-replay-v1`; GitHub and remote match.

**Q2. Is the seam file forbidden/protected?** YES. `run.py` is supplemental protected controller evidence under the read-only source policy.

**Q3. Was a post-commit hook or wrapper fallback used?** The forbidden-safe wrapper/decorator fallback. It records the exact frozen `solve_QP` output, then performs immutable capture at entry to the frozen plant function after the protected caller has passed its success guard and before plant evaluation.

**Q4. Was the controller main loop copied or rewritten?** NO.

**Q5. Is selected `u_k` captured after commit and before plant update?** YES. Reaching the decorated plant entry proves `run.py` passed its success guard; snapshot/enqueue occur before the exact original plant function is called at `run.py:147`.

**Q6. Is `u_des` counted as a native alternative?** NO. It is only `NOMINAL_REFERENCE`; native group size is one without genuine siblings.

**Q7. Does the payload share production mutable storage?** NO. It contains frozen dataclasses, tuples and scalars after an independent copy.

**Q8. Does worker payload remain unchanged after source mutation?** YES. Aliasing and post-enqueue source-mutation tests pass.

**Q9. Are enqueue and receive semantic hashes equal?** YES in the task-local worker test; mismatches become `PAYLOAD_ALIGNMENT_FAILURE` with no L2 result.

**Q10. How many static full-map hashes occur per run?** Exactly 1.

**Q11. Is a full map hash recomputed per step?** NO; each step records only `map_authority_id`.

**Q12. Are L0/L1/L2 side-effect-free or isolated on worker-owned inputs?** YES at this implementation boundary: frozen certificate functions are read-only over immutable payloads, map/backend dependencies are worker-owned, and the actual frozen H1 function passed a purity test.

**Q13. Does queue full wait for the controller?** NO. `put_nowait` immediately returns `DROPPED_QUEUE_FULL`.

**Q14. Does worker crash change action?** NO. Fault QA preserves the mock selected control and return value.

**Q15. Is there any result-return channel?** NO. Static API/AST audit count is zero.

**Q16. Is instrumentation failure recorded as L2 `UNKNOWN`?** NO. Health and L2 status are separate schemas; no valid L2 evaluation means no L2 result.

**Q17. Was real OFF-vs-ON navigation equivalence run?** NO, count 0.

**Q18. Was a logging pilot run?** NO, count 0.

**Q19. Was a formal on-policy cohort collected?** NO, count 0.

**Q20. What is the strongest current claim?** Non-invasive shadow instrumentation has been implemented and passed task-local/static/fault QA, pending real OFF-vs-ON control-trace equivalence validation.

**Q21. What is next?** `VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1` only, under separate authorization.

## Evidence summary

The frozen controller identity is `run.py` at blob `361f09fc8f37e4713ea2fc8975d82d56cb9be46a`. The six-state is formed at lines [101, 102]; `v_k=x[3:]`; `dt=0.05` at line 19; `u_des` at line 125; selected `u` at line 132; the solver failure guard begins at line 139; plant propagation is line 147.

Because direct modification is forbidden, the wrapper delegates without copying `run.py`, reimplementing `solve_QP`, or reimplementing the plant. It returns the exact selected Python object, then the plant decorator captures and calls the exact original plant. Capture exceptions, backpressure and worker failure are contained. The append-only logs join by explicit run/trial/step/state/commit/payload/candidate/map IDs.

The F1-F10 matrix passes all expectations and all mock OFF/fault traces are equal. This is structural fault QA, not real navigation equivalence. Four independent reviewers recommend Case A with no critical blocker and agree on the narrow claim boundary.

## Decision

`FINAL_STATUS=PASS_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_IMPLEMENTATION_V1`

`FINAL_DECISION=FREEZE_INSTRUMENTATION_AND_VALIDATE_OFF_VS_ON_CONTROL_TRACE_EQUIVALENCE`

`Only next task=VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1`
