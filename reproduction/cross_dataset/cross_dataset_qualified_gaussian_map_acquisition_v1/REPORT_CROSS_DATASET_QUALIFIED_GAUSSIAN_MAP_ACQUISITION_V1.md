# Cross-Dataset Qualified Gaussian Map Acquisition, Qualification and Selection V1

## Final outcome

- `FINAL_STATUS`: `BLOCKED_BY_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED`
- `FINAL_DECISION`: `REQUEST_USER_TO_ACCEPT_SCENESPLAT_AND_COMPONENT_TERMS`
- Sole next task: `RESUME_EXTERNAL_GS_MAP_ACQUISITION_AFTER_ACCESS_APPROVAL_V1`

## 1. Why the task does not bind to more self-map training

The frozen TUM and Replica mapping routes are retained as prior evidence. This task tests the separate input-qualification question for independent pretrained maps; it does not train, fine-tune, repair, or select a map from controller outcomes.

## 2. Frozen route decisions and claim boundary

The TUM safety-case route remains closed for navigation benchmarking; Splatfacto, SplaTAM, and official-config Gaussian-SLAM mapping routes remain closed as recorded in `frozen_mapping_route_decisions.json`. None establishes mapping frontend or navigation generalization.

## 3. Official SAFER scene inventory and static G0

Authority identity match: `True`. Loadable official scene configurations: `4`. Static-G0-ready scenes: `4`; non-Stonehenge ready scenes: `3`. Each attempted scene is checkpoint load-only and uses 32 deterministic static queries repeated three times; no controller or navigation call is made.

## 4. External source, license, and access gate

The frozen primary source is Hypersim (`GaussianWorld/hypersim_mcmc_3dgs`) with `GaussianWorld/scene_splat_7k` as metadata registry; ARKitScenes remains only a frozen fallback. The server had no verified read-only token, no installed HF CLI/client, no pre-existing external pretrained map, and its public Hugging Face API checks were unreachable. This task neither accepts terms on the user's behalf nor bypasses a gate.

## 5. Metadata ranking, primary/backup registry, and download budget

No metadata was downloaded; ranked candidate count is zero and no primary or backup identity is frozen. Downloaded external bytes are zero of the 20 GiB limit. Consequently no scene archive, language feature, full snapshot, or unknown mirror was acquired.

## 6. Parameter semantics, canonical export, and metric coordinates

These stages are explicitly `NOT_AUTHORIZED_DUE_TO_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED`. No map array was decoded or transformed; no filtering, scale fitting, Sim(3), ICP, or coordinate repair took place.

## 7. Held-out evaluator, geometry, structure, and G0

No external held-out registry, renderer binding, geometry metric, structure audit, or external G0 result exists. The PR58 fixture constants are retained only as a frozen reference, not represented as an executed external-evaluator pass.

## 8. Selection and downstream boundary

No external map is selected or qualified. No SAFER/FAS-CBF cross-dataset benchmark, navigation, CBF-QP, Start-Safe, Risk-Aware, Discrete Verification, Recovery, or TUM work was run.

## 9. Recovery instruction

After the user has enabled an approved server-side access route and accepted applicable terms, resume exactly at `RESUME_EXTERNAL_GS_MAP_ACQUISITION_AFTER_ACCESS_APPROVAL_V1`. Reuse the frozen route decisions and ranking rule; do not rerun any closed mapping route.

## Evidence files

- `frozen_inputs/frozen_mapping_route_decisions.json`
- `official_safer_inventory/official_safer_scene_inventory.json`
- `official_safer_inventory/official_safer_scene_static_compatibility.json`
- `access_and_license/external_dataset_access_and_license_audit.json`
- `run_manifest.json`, `validation_result.json`, and `downstream_handoff.json`
