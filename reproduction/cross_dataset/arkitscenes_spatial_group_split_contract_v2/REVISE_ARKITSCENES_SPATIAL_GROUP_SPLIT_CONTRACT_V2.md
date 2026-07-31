# ARKitScenes Spatial Group Split Contract V2

This tracked root revises only the allocation of complete, immutable V1 spatial groups to TRAIN and HELDOUT. It does not change candidates, raw data, joins, keyframes, grouping, coordinate validation, SplaTAM configuration, geometry gates, seeds, or PR #67 conclusions.

The V2 eligible scene must retain at least 240 V1 keyframes and use `target_heldout=floor(0.20*N+0.5)`, complete groups only, `40 <= HELDOUT <= 60`, `TRAIN >= 200`, no discard, and the prescribed deterministic score `(abs(H-target), H, selected_group_hash_tuple)`.

This is split protocol only: no mapping training, no geometry result, no SplaTAM smoke, no checkpoint, no controller benchmark, and no new ARKitScenes download.
