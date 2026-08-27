# REPORT: Design L2/H1 On-Policy Shadow Observation V1

## Direct answers to the 20 required questions

**Q1. PR #95 frozen replay exposed which three largest evidence gaps?** Numeric selected `u_k` was absent in 4,259 non-replayable records; L2 reachability was unknown in 5,795 records; candidate/map provenance was incomplete enough that executed and non-executed rates could not share one denominator and map replay required external authority recovery.

**Q2. Why not production-integrate L2 next?** PR #95 proved a bounded shadow information signal under incomplete historical replay, not control efficacy or non-invasiveness. Instrumentation, zero-feedback, alignment, and equivalence must be implemented and validated first.

**Q3. What is the real selected `u_k` source?** In frozen `run.py`, `u = cbf.solve_QP(x,u_des)` at line 132; `cbf/cbf_utils.py:125-143` returns the QP output and `run.py:139-143` accepts it only when `solver_success` is true.

**Q4. Where is final decision commit?** Semantically after the success guard at `run.py:139-143` and before the selected action is applied to the plant at `run.py:147`.

**Q5. How will L0/L1/L2 reachability be recorded?** The isolated read-only worker writes reached/status/reason for frozen current-feasibility L0, immediate-segment L1, candidate preparation, and L2 at evaluation time under source class `SHADOW_PIPELINE_RUNTIME_OBSERVATION`; no post-hoc inference.

**Q6. Which architecture and why?** Option A: post-commit immutable tap plus bounded nonblocking queue and out-of-process worker. It uniquely combines correct `x_k/u_k` visibility with crash isolation and structural zero authority.

**Q7. How can results not feed back?** There is no worker-to-controller interface, shared mutable control object, result callback, or controller result consumer. All authority flags are false; the worker writes append-only evidence only.

**Q8. What happens on queue full or worker crash?** The frozen controller continues its original path with the already committed `u_k`; the observation is marked dropped/incomplete when possible.

**Q9. How is mass `u_k` missingness prevented?** Numeric `u_k` and its canonical hash are mandatory in the immutable post-commit payload, and G2 rejects any complete payload without them while all intended steps reconcile to payload or drop records.

**Q10. How is map authority replayable?** A run-start manifest hashes immutable config/checkpoint/map bytes, representation and robot/margin/rho contracts; every step joins by stable `map_snapshot_ref`. Dynamic maps would require per-step content-addressed snapshots.

**Q11. How is the executed primary cohort defined?** True frozen-controller on-policy steps with committed selected/executed candidate, stored shadow L1 PASS, explicit L2 reach, and a completed formal L2 PASS/FAIL/UNKNOWN result.

**Q12. How are native non-executed secondary candidates defined?** Controls already created by the frozen controller before observation, carrying native origin/role/hash and `selected_for_execution=false`; they are analyzed separately.

**Q13. Any synthetic candidates?** NO. Candidate synthesis count is zero.

**Q14. Future primary endpoint?** `P(L2_FAIL | stored_L1_PASS, L2_reached, selected/executed candidate, L2 evaluated)` with explicit numerator and denominator.

**Q15. Can L1 PASS/L2 FAIL be called collision prevented?** NO. It is a candidate-dependent future-safety shadow signal or L2-specific information increment only.

**Q16. L2 UNKNOWN versus logging incomplete?** L2 UNKNOWN requires a valid formal evaluation unable to certify; missing/queue/serialization/alignment/worker failures use separate observation and health states and never enter UNKNOWN.

**Q17. What is the pre-collection equivalence gate?** Fixed-seed/config/map OFF-vs-ON comparison requiring equal selected-candidate/control/branch/return/termination traces under pre-frozen exact or field-specific tolerances.

**Q18. How does stopping avoid optional stopping and iid-step errors?** The primary plan fixes all 100 Stonehenge trials before results and never stops on FAIL count. Uncertainty resamples trials/uses trial-level summaries; step-level iid significance is not primary.

**Q19. Did this task collect any on-policy data?** NO. `on_policy_collection_count=0` and `navigation_rollout_count=0`.

**Q20. Is the next step formal data collection?** NO. Under Case A the only next task is `IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1`; implementation and validation must precede any separately authorized collection.

## Frozen identity and static audit

PR #95 was independently verified Open Draft at `a7fd936804284a299467f1bfcc76deab12fdf0c3` on `l2-h1-shadow-frozen-replay-v1`, based on `l2-h1-shadow-certifier-v1`. PRs #83/#84/#86/#87/#89/#90/#91/#92/#93/#94/#95 were preserved read-only. The upstream 17-blob protected manifest passed raw Git blob, byte size, and mode audits.

The primary controller seam is exact: `x` is the six-state at `run.py:100-116`; `u_des` is formed at lines 118-127; QP-selected `u` at line 132 is accepted by lines 139-143; plant propagation occurs at line 147. Capture between acceptance and propagation prevents state/action index drift. Current logging at lines 149-152 occurs too late for a robust same-decision contract.

PR #89's richer frozen runtime also shows that native alternatives are created before commit, but its result retains candidate identity without the final acceleration. This independently demonstrates why the future payload must copy numeric control at the seam.

## Architecture and zero authority

Option A is selected and Option B wrapper/decorator is fallback. Option C pure sidecar from current logs cannot restore missing fields; Option D post-plant scraping is rejected. The future tap only makes an immutable copy and nonblocking enqueue. L0/L1/L2 run only in the sidecar and have no decision authority. Queue full, serialization error, worker crash, result lateness, and shutdown incompleteness affect observation completeness only.

The primary `run.py` baseline does not execute PR #84 L0/L1 stages, so the design labels worker-computed stages precisely as runtime shadow-pipeline observations. It does not falsely call them production-controller outcomes. That instrumentation-only future implementation does not alter controller mathematics.

## Cohort, denominator, and statistics

The primary executed cohort is separate from native non-executed candidates. The production baseline contributes nominal and selected native values; richer alternatives are included only where the frozen runtime already generates them. If a runtime has one native candidate, count is one. Secondary alternative analysis is `NOT_ESTIMABLE` when alternatives are not natively exposed; this never blocks the primary cohort.

Every intended control step enters `N_control_steps_all`, including drops. L2 reach, evaluation, PASS/FAIL/UNKNOWN, native candidates, multi-candidate groups, drops, logging errors, and worker errors have disjoint counters. No cohort is constructed from observed L2 outcomes.

Planning uses 6/566 selected FAIL and 18/788 overall L1 PASS/L2 FAIL as biased priors only. Plan A freezes all 100 deterministic Stonehenge trials. Plan B pre-freezes a 566-evaluated target plus the same 100-trial cap and stops only at trial boundaries, never on outcomes. Cluster-aware trial bootstrap/trial aggregation is primary uncertainty.

## Future phases and gates

Phase 0 is implementation QA; Phase 1 is excluded equivalence smoke; Phase 2 is excluded completeness pilot; Phase 3 is a separately authorized frozen cohort; Phase 4 is analysis only. Ten kill gates cover control trace, `u_k`, reachability, map authority, zero feedback, queue nonblocking, provenance, protocol freeze, state/action alignment, and health/status separation.

## Reviews and claims

All four independent reviewers return `PASS_DESIGN_ONLY`, no critical blockers, and Case A. Their minor cautions are frozen as future requirements: distinguish worker L0/L1 from controller outcomes, freeze capacity without outcome tuning, treat old rates only as biased priors, and prove immutable device-to-host copies.

Supported now: feasibility of this design. Future valid Phase 3 can support only prospective signal/information/prevalence/completeness/map-relative mechanism descriptions. It cannot support collision reduction, progress improvement, controller efficacy, intervention success, recursive feasibility, safe stop, physical safety, deployment, real-time performance, or superiority.

## Decision

`selected Case = CASE_A — FEASIBLE_NONINVASIVE_ON_POLICY_SHADOW_DESIGN`

`FINAL_STATUS = PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_V1`

`FINAL_DECISION = FREEZE_ON_POLICY_SHADOW_PROTOCOL_AND_IMPLEMENT_NONINVASIVE_INSTRUMENTATION`

`Only next task = IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1`

No unresolved blockers. No implementation or collection is authorized by this report.
