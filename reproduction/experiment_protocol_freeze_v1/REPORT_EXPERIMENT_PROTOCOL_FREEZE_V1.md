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

H1/H2/H3 are registered verification horizons. H3 is the more conservative offline reference horizon under the same-model rollout; H2 may be a practical configuration only where separately evidenced.

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

The package establishes protocol/provenance readiness for a separate G0 portability audit; it does not authorize G1 baseline reproduction. G1 requires separate authorization and completed target-specific gates. This is not a cross-dataset proof, a new experiment, an R1 activation, or a new CBF theorem.

Validation status is written to `validation_result.json`; bundle integrity is written to `freeze_bundle_sha256.json`.

## Pre-Freeze Cross-Dataset Evidence Revision

This provenance-only revision registers work that occurred before Freeze V1. No new data processing, rendering, training, SAFER loader/baseline, or Cross-Dataset method evaluation was run.

Replica historical source branch/commit: `safer-replica-frozen-render-protocol-v1` / `fe250df543aa158557c176ee4f87dc131bb61e60`; it is historical external lineage, not a current-HEAD ancestor. The isolated Python 3.9 renderer closure, fixed 300-frame protocol, and manifest are source-recorded. The manifest hash is `1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25`. RGB/depth integrity blocked V1: 33 black/near-black RGB frames and 32 all-zero depth frames. No frames were deleted, replaced, or rerendered; no training or SAFER run occurred. Replica remains `blocked_by_rgb_integrity`, cannot enter training/G1, and requires separately authorized Replica V2 diagnosis.

TUM historical source branch/commit: `safer-cross-dataset-metric-preprocessing` / `3e22a7cae6f4c3c2c192cc2d7af3c9fbd607a0a3`; it is also historical external lineage. Metric RGB/depth/pose preprocessing and transforms provenance are recorded, including transforms SHA-256 `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`. Its GSplat checkpoint, adapter, ellipsoid query, benchmark/evaluator, and dynamics gates remain unfinished; TUM is G0 pending and G1 blocked.

The validator now separates historical method-freeze readiness from Cross-Dataset provenance and G0/G1 readiness. It reports critical/noncritical unresolved fields. The 21 algorithm configuration IDs are unchanged; no core source was modified. PR #21 is Draft. This revision does not claim renderer output equals generalization, preprocessing equals reconstruction, reconstruction equals SAFER portability, or integrity failure equals SAFER failure.
