# ARKitScenes SplaTAM M1 smoke and learned-map qualification V1

This tracked capsule records the immutable protocol implemented by this directory. The full user-authorized protocol remains the authority when this capsule is silent.

## Frozen inputs and execution

- Scene `48018874`; deterministic V2 split with 214 TRAIN and 53 HELDOUT frames.
- M1 uses positive depth with confidence greater than or equal to one; TRAIN rows 76 and 79 are the only zero-valid frames.
- SplaTAM GT-pose map-only, seed `20260730`, physical GPU 1, official 7,000-iteration mapping semantics.
- The empty-depth-safe compatibility layer may only make exact zero-valid frames contribute zero depth loss and zero Gaussian additions. It may not change nonempty behavior.
- HELDOUT is unavailable to mapping and becomes readable only after a complete formal map and deterministic canonical export.
- One scientific formal result is accepted. Scientific failure cannot be retried, tuned, resumed, filtered, rescaled, aligned, or replaced.

## Frozen gates

- Two bounded smoke runs must pass, including the exact rows 76/79 policy and return to the nonempty path.
- Canonical arrays must be finite and semantically converted exactly once; two fresh export trees must be byte-identical.
- All 53 HELDOUT frames must render with finite NVS metrics and no map mutation.
- Primary confidence>=1 depth gates: coverage>=0.95, AbsRel<=0.20, delta1>=0.75, median predicted/GT ratio in [0.80,1.25], and zero nonfinite values.
- Confidence==2 depth is report-only. A 10x, 100x, or 1000x scale signature is a coordinate/scale failure and may not be repaired post hoc.
- Clearance and three fresh SAFER static G0 processes run only after the Primary depth gate passes.

## Fail-closed result contract

All gates passing yields `PASS_ARKITSCENES_SPLATAM_M1_LEARNED_MAP_QUALIFIED` and the only next task `FREEZE_ARKITSCENES_EXECUTABLE_SAFETY_AND_PLANNER_BENCHMARK_V1`.

Any frozen scientific map gate failure yields `NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT`, closes the ARKitScenes mapping route after this final M1 attempt, publishes no map, and permits only `ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1` next. M2, another variant, hyperparameter search, frame deletion, opacity filtering, ICP/Sim3/scale repair, controller execution, and checkpoint reuse are forbidden.
