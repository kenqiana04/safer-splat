# Metrics and Failure Taxonomy

## Metric semantics

| Term | Frozen definition | Not equivalent to |
| --- | --- | --- |
| collision | The registered collision predicate reports a physical collision event for a trial | An `h` margin violation |
| collision-free | `collision_count == 0` for the registered trial/run | A proof of continuous-time safety |
| margin violation | A registered current, predicted, base-horizon, or executed-horizon `h` value is below its stated margin | Collision |
| warning | A configured predictive/current safety condition crosses the registered warning threshold | A recovery success/failure |
| predicted horizon safety | Minimum `h` on the rollout used for an evaluator's prospective decision | Executed horizon safety |
| executed horizon safety | Minimum `h` after the selected control is executed and checked in the recorded wrapper | Meter clearance |
| QP infeasible | The CBF-QP solver returns infeasible under the registered implementation | Collision or a failed recovery search |
| recovery failure | A triggered predictive recovery has no candidate meeting the registered criterion | Global local controllability failure |
| progress | The implementation's recorded goal-progress metric | Goal reached unless separately marked |
| runtime | The recorded timing statistic with its scope and warm-up policy | A hardware-independent speed claim |

`h` is the repository GSplat ellipsoid safety field. It is **not meter clearance**, and negative/positive `h` must not be converted to a distance without a separately validated mapping. A margin violation is not collision; a collision-free count does not erase negative margin evidence.

## F1--F8 failure taxonomy

| ID | Name | Operational signal | Allowed interpretation |
| --- | --- | --- | --- |
| F1 | Dataset/checkpoint reachability | Missing/ambiguous data, config, checkpoint, or start-goal source | Block G0/G1 until provenance is fixed |
| F2 | Initial-state feasibility | Initial safety certification is near-unsafe/unsafe | Separate original from post-repair outcomes |
| F3 | Collision | Registered collision predicate fires | Report collision; do not relabel as margin only |
| F4 | CBF-QP infeasibility | QP solver reports infeasible | Record solver event separately from collision |
| F5 | Predictive warning/margin | Current or H-step `h` crosses registered threshold | Diagnostic/trigger signal, not collision |
| F6 | Recovery-search exhaustion | No candidate meets the fixed recovery criterion | Local, contract-bounded failure only |
| F7 | Interface/provenance mismatch | Helper, config, schema, or parameter mismatch | Block comparison until resolved |
| F8 | Runtime/measurement invalidity | Mixed hardware, warm-up, units, or timing scope | Do not compare runtimes |

## Claim boundary matrix

- Initial repair success does not repair the original benchmark record.
- A zero collision count does not certify positive `h` at every evaluated horizon.
- A successful HCE Stage-A selection does not show that Stage-B recovery succeeds.
- A failed GTEP shadow primitive does not disprove all directional recovery designs.
- Runtime ratios apply only to the logged scope and hardware context.
