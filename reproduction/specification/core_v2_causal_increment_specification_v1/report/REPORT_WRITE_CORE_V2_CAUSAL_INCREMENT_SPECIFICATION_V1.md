# REPORT: Write Core V2 causal increment specification V1

## Answers first

1. **Why B1 cannot be a candidate discriminator:** under the frozen model `Segment(p_k,p_(k+1))` has zero position derivative with respect to `u_k`.
2. **Why H1 is first affected:** `u_k` changes `v_(k+1)`, which determines `[t_(k+1),t_(k+2)]`; `u_(k+1)` cannot change position until the next segment.
3. **Candidate dependence:** proved as `d p_H1(alpha)/d u_k=alpha*dt^2*I`, nonzero for every `alpha>0`.
4. **Backend reuse:** yes; the frozen arbitrary-endpoint segment backend can receive `S_H1` without changing geometry.
5. **Certificate class:** exact analytic for frozen isotropic spheres; conservative lower bound for general frozen ellipsoid signed-distance semantics; dense sampling remains diagnostic only.
6. **Continuous segment:** yes for both formal backends over all `alpha in [0,1]`; endpoint fallback is disabled.
7. **Map/robot/margin/UNKNOWN:** sufficient for a map-relative specification: static snapshot, represented closed primitives, 0.10 m ball plus 0.01 m margin, and typed fail-closed UNKNOWN/nonfinite behavior.
8. **What L2 proves:** local candidate-dependent map-relative safety of the first control-affected segment under frozen assumptions.
9. **What L2 does not prove:** future/recursive/physical/robust/real-time/deployment safety, recoverability, safe stop, or performance.
10. **Why L2 cannot replace L3:** H1 safety does not establish a backup witness or terminal reachability.
11. **Why H1 is not recursive feasibility:** it covers exactly one local segment and specifies no invariant or future policy.
12. **Why H2 is unnecessary now:** H1 closes the first causal gap with fewer assumptions; H2 requires a later-control witness and is deferred.
13. **Required upstream mutations:** none; dynamics, map, controller, B0-B3, library, backup, terminal set, and thresholds remain frozen.
14. **Falsification gates:** G1-G7 all PASS with explicit counterevidence conditions.
15. **Shadow-only next step:** yes, but only under a separate authorization; it must have no controller authority.

## Decision

`PASS_CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION`

`FREEZE_MINIMAL_L2_H1_SPECIFICATION_AND_VALIDATE_IN_SHADOW_ONLY_MODE`

Selected case: `CASE_A`. Only next task: `IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1`.

## Boundary

This task performed no implementation, training, map/data/cohort change, controller/method/dynamics change, formal B0-B3 run, navigation rollout, oracle, sweep, benchmark, parameter tuning, or formal GPU compute. Historical evidence was preserved and not upgraded.
