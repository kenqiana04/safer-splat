# ARKitScenes raw SplaTAM learned-3DGS qualification V1

`FINAL_STATUS=BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT`

## Decision

The task stopped before creating an independent SplaTAM environment, smoke, baseline, checkpoint, canonical map, rendering, clearance audit, G0, or controller benchmark. The frozen spatial-group split gate failed for both pre-frozen candidates; no threshold, group, pose, scale, or mapping parameter was changed.

## Authority and access

- Apple ARKitScenes commit: `7283761bf26c27570ec59a5dc0f8686fbff07726`
- Official download script SHA-256: `1eca7fb832aab84c15da8ed5ffe38d4f1f7ffb4256fcfd755ef4b39a31b48137`
- Official SplaTAM commit: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
- Access preflight passed through the task wrapper.
- FARO-to-ARKit join remains not authorized; FARO download count is zero.

## Deterministic candidates

- PRIMARY: visit `434897`, video `42899163`, hash `00003085438b20460b41f02d8dd484408a0bc9da3d1d0d61912721cfecdeaac0`.
- BACKUP: visit `483945`, video `48018874`, hash `000d603a86bb18727932cd9b5e936583b323300d756b455b518de83054c60b87`.
- Both completed official raw-asset validation, strict RGB-D-confidence-intrinsics-pose joins, metric depth-to-mesh coordinate audits, and future hard-benchmark geometry prechecks.
- No third candidate was downloaded.

## Blocking split evidence

- PRIMARY: 173 keyframes; TRAIN=0; HELDOUT=0; status `BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT`.
- BACKUP: 267 keyframes; TRAIN=240; HELDOUT=0; status `BLOCKED_BY_ARKITSCENES_DATA_OR_COORDINATE_CONTRACT`.
- The contract requires an exact 240/60 split when possible, otherwise at least 220/50, with no group splitting. Neither candidate meets the minimum.

## Boundaries preserved

- training=0; smoke=0; controller benchmark=0; checkpoint=false; formal map=false.
- No ICP, Sim3, pose-scale fitting, threshold relaxation, group splitting, or third-candidate fallback was performed.
- No ARKitScenes learned-map qualification or downstream hard-benchmark handoff was created.

## Required next action

No automatic next task is authorized. Any reconsideration of the split contract or candidate-selection protocol requires separate explicit authorization.
