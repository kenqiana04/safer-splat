# REPORT: Experiment Protocol, Configuration, Trial and Commit Freeze V1

## 1. Scope

This is a formal evidence/protocol freeze for later Cross-Dataset Baseline Portability/Generalization Audit. No GPU experiment, rerun, planner test, or cross-dataset evaluation was performed.

## 2. Repository identity

Freeze parent: `41ccb54d2e9f10c0b3b559431a58a5763977d462` on `v4c-geometry-tangential-primitive-shadow`.

## 3. Frozen method statement

The frozen wrapper statement is **Certified Feasibility-Aware Start-Safe CBF + Discrete-Time Verification + Optional Triggered Predictive Recovery**.

## 4. Baseline role

SAFER-Splat remains a comparator. This freeze does not present baseline behavior as a novel contribution.

## 5. Risk-Aware V1 role

Risk-Aware V1/bestD is retained as efficiency-support evidence and a component of the recorded wrapper, not as a standalone safety theorem.

## 6. Start-safe role

Initial-state certification and repair are retained with original and post-repair results separated.

## 7. DT verification role

H1/H2/H3 are registered verification horizons. H3 is the robust reference; H2 may be a practical configuration only where separately evidenced.

## 8. V4-B status

V4-B is a negative diagnostic under the tested Euler double-integrator rollout, not a general impossibility result.

## 9. V4-C status

V4-C is an optional, warning/on-margin-triggered predictive recovery component under its fixed H/N/margin contract.

## 10. HCE status

HCE V0 is retained only as held-out recovery-search efficiency evidence. It does not claim more recovery capability.

## 11. SAFC/R1 status

SAFC/R1 remains paused. Its records are provenance/diagnostic material, not an active candidate for the upcoming audit.

## 12. Adaptive/warning/VANS status

AdaptiveV1, warning slowdown, and VANS remain diagnostic/support configurations until independently registered for a formal comparison.

## 13. Trial-20 status

Trial 20 is a targeted local recovery-exhaustion diagnosis. It is not a tuning case, planner evaluation, or safe-halt result.

## 14. GTEP status

GTEP V0 was shadow-only. Its zero feasible opportunity result is negative evidence under a fixed local contract, not a rejection of all directional recovery.

## 15. Dataset registry

Stonehenge and dense flight checkpoint paths are source-recorded in `dataset_registry.yaml`. Any new dataset must pass G0 reachability before a baseline run.

## 16. Trial registries

The freeze contains official100 registries, the 8 repair-needed cohort, development trials 12/13/14, a held-out activated cohort of 16 trials, and 34 ordered trial-20 contexts.

## 17. Cohort isolation

Development `[12, 13, 14]` is disjoint from the held-out cohort. Original and post-repair outcomes cannot be pooled.

## 18. Metric semantics

Collision, QP infeasibility, warning, margin violation, predicted safety, and executed safety are separately defined in `METRICS_AND_FAILURE_TAXONOMY.md`.

## 19. Safety-field boundary

The repository GSplat ellipsoid `h` field is not meter clearance. A margin violation is not a collision, and collision-free status does not erase negative margin evidence.

## 20. Failure taxonomy

F1--F8 cover reachability, initial-state feasibility, collision, QP infeasibility, warning/margin, recovery exhaustion, interface/provenance mismatch, and runtime measurement invalidity.

## 21. Configuration integrity

The config registry has 21 required module identifiers. Source-supported values are frozen in JSON; unknown historical fields remain unresolved instead of being inferred. No H/N/margin conflict is recorded.

## 22. Commit/provenance integrity

Nine historical commits are audited for object existence and ancestry. The source-file inventory records path, Git tracking, last commit, role, size, and SHA-256.

## 23. Decision and limitations

The package establishes protocol readiness for a separate G0 portability audit and, only after target provenance is complete, G1 baseline reproduction. It is not a cross-dataset proof, not a new experiment, not an R1 activation, and not a claim of a new CBF theorem.

Validation status is written to `validation_result.json`; bundle integrity is written to `freeze_bundle_sha256.json`.
