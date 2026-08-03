# ARKitScenes Supervision Contract V1 to V2 Rationale

## Preserved V1 result

PR #72 remains formally `NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED` with decision `CLOSE_ARKITSCENES_SPLATAM_MAPPING_ROUTE_WITHOUT_TRAINING`. This task does not rewrite or retroactively pass V1.

## V1 diagnosis

`PREREGISTERED_FIXED_GROUP_COUNT_GATE_ARITHMETICALLY_INFEASIBLE_FOR_SMALL_GROUPS`

V1 required at least 10 supported frames in every group. Frozen TRAIN group sizes are `[24, 18, 42, 1, 2, 24, 9, 94]` for group IDs `[0, 1, 2, 3, 6, 9, 11, 12]`. Groups 3, 6, and 11 have only 1, 2, and 9 frames, so no mask can supply 10 supported frames without violating the split or adding data.

## V2 scope and formula

V2 is a `POST_AUDIT_PRETRAINING_PROTOCOL_REVISION`. It changes only the supported-count arithmetic to `S_g >= max(1, ceil(0.80*N_g))`. Global retention, global frame support, temporal run, per-frame support definition, and per-group pixel retention are unchanged. There is no geometry relaxation, threshold search, mask search, frame deletion, regrouping, or learned-map result tuning.

## Result

M1 passes every unchanged gate and every normalized group gate. Three fresh processes produced byte-identical results. V2 therefore permits compatibility qualification only; it is not mapper, smoke, training, or learned-map evidence.
