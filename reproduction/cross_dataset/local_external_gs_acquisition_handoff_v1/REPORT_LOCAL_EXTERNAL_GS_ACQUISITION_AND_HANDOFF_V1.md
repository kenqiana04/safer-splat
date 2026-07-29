# Local External GS Acquisition and Verified Handoff V1

## Final outcome

- `FINAL_STATUS`: `NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD`
- `FINAL_DECISION`: `DO_NOT_DOWNLOAD_AN_UNQUALIFIABLE_SCENE`
- Sole next task: `SELECT_ONE_FINAL_PUBLIC_PRETRAINED_GS_SOURCE_V1`

## Local access and immutable sources

The user-approved Hugging Face access gate passed. Metadata registry revision: `685f9e9053b8dcc2a23100eb52f64ee4711b0875`. Hypersim component revision: `f85e166ac72fa8367bf616c4dbce87749b748e81`. Seven official metadata/card/manifest files (167,251 bytes total) were materialized as ordinary local files; no map payload was downloaded.

## Published ranking and precheck

The frozen ordering was depth_l1 ascending, PSNR descending, Gaussian count ascending, then scene ID. The top ten resource-range candidates were evaluated from published statistics. The leading two were `hypersim_ai_001_006` and `hypersim_ai_008_003`.

## Why no map was downloaded

Both leading transforms files contain 300 and 200 training frames respectively but zero test frames. The official frozen component tree supplies no scene-specific minimal held-out RGB payload or GT depth/mesh manifest. The original Hypersim source documents scene archives rather than a frozen 30-frame component manifest. The allowed fallback `GaussianWorld/arkitscenes_mcmc_3dgs` returned HTTP 404. Therefore neither a primary nor backup can be frozen without violating the no-guessing and no-overdownload rules.

## Boundary

Downloaded map bytes, map modification, training, canonical export, geometry evaluation, SAFER G0, navigation, CBF-QP, and package files are all zero. This is not map qualification or navigation readiness.
