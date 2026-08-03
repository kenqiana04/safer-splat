# REPORT: ARKitScenes SplaTAM M1 learned-map qualification V1

## Result

- `FINAL_STATUS=NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT`
- `FINAL_DECISION=CLOSE_ARKITSCENES_MAPPING_ROUTE_AFTER_FINAL_M1_ATTEMPT`
- `Only next task=ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1`
- No ARKitScenes map was selected or published. The route was closed after the one frozen M1 formal attempt.

## Git and scope

- Branch: `arkitscenes-splatam-m1-learned-map-qualification-v1`
- Base branch/head: `arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2` / `3fe598dc497cc36b6848d2b9bf19c13955874199`
- Scene: `48018874`; TRAIN/HELDOUT: `214/53`; seed: `20260730`; physical GPU: `1`
- Mapper role: `SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY`
- HELDOUT mapper access count: `0`

## Frozen identities

- ARKitScenes authority: `7283761bf26c27570ec59a5dc0f8686fbff07726`
- SplaTAM authority: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
- Diff Gaussian rasterizer authority: `cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`
- TRAIN SHA-256: `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`
- HELDOUT SHA-256: `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`
- TRAIN/HELDOUT Git blob OID: `a2ddc70775e6d0f9c25f77ef5f869556d83b292c` / `cf28dd385711a31733360e5fc21dce229ce605bc`
- Split/group tuple SHA-256: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee` / `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`
- M1 compatibility SHA-256 / Git blob OID: `8930c9d2e5172d0c56e698a418b3f454171e6c9fd84e3079d1f7c3568436a6f3` / `b134d45f68f8de060f94f8867dfb173c98be8f0b`
- M1 valid pixels: `9277821`; zero-valid TRAIN indices: `[76, 79]`
- Runtime patch SHA-256: `18f03bd15fc8b8243c4dd1d092e15bc70e23df92913186124c80fba1a3f1c840`; formal config SHA-256: `49c2c085e04bb08d9edf10e12ed117e1fec4ddeac240c07f76761689f3ed05bc`
- Environment: `/disk1/zlab/conda_envs/arkitscenes_splatam_canonical_v1`; Python `3.10.20`; PyTorch `2.1.2+cu118`; CUDA runtime `11.8`; NumPy `1.26.4`; NVIDIA driver `525.147.05`.
- Runtime overlay: `/disk1/zlab/maintenance_records/arkitscenes_splatam_canonical_learned_map_qualification_v1/environment/runtime_overlay_setuptools_81_0_0`.
- Evaluator registry SHA-256: `6ac5ac290463365a9daa7d6d3ccc30db406f00b34a13a04ef224b52cf6dd9a7f`
- Clearance/G0 registry SHA-256: `0c26376a7dcecda99c02b86a716f455513a41d816c7b14e1384054edba2c10c5` / `50fa0f07235554488cd29f6049cc1cbbf8689e14447d46e7d2a95c875fc3d96d`
- Execution-lock SHA-256: `8dea43390816f92b03347a91b9c59ba28b822175b8bce25b7e578c7b9f865f54`

## Qualification stages

- Input, task-owned runtime, frozen config and evaluator registries: PASS.
- PR #73 compatibility revalidation: synthetic nonempty equivalence PASS, synthetic zero-mask PASS, real nonempty forward equivalence PASS, real zero-frame PASS, sequence-state dry run PASS, first-frame M1 nonempty PASS.
- Smoke A rows 0-11: `PASS_SMOKE_MAPPER_RUN`, 629,294 Gaussians, 7,000 finite optimizer steps.
- Smoke B rows 70-82: `PASS_SMOKE_MAPPER_RUN`, 782,185 Gaussians, 7,000 finite optimizer steps.
- Smoke B rows 76/79: exact empty-safe events, exact zero depth loss and zero Gaussian additions; rows 80-82 returned to the nonempty path.
- Formal attempt: one process, one completed output, no retry, 214/214 frame events, 7,000 finite optimizer steps, rows 76/79 exact empty-safe, no checkpoint.
- Formal runtime to final params: `1140.174` seconds; monitored process RAM peak sample: `8.3%` of 67,294,916,608 bytes (about 5.20 GiB); monitored GPU-memory peak sample: about `5.4 GiB`.
- Formal map: `6,463,948` Gaussians; params SHA-256 `86ba75c9db0fab1a5eb7d65da82454514419a30d7bea6df68b2bbc0518000193`; size `310292404` bytes.
- Two fresh canonical exports: `PASS_TWO_FRESH_CANONICAL_EXPORTS_IDENTICAL`; tree SHA-256 `e1326f0ac5519fa1c743b9bde448a5584bc3062e61e3dccedac870fadbe977c7`; no filtering, recentering, scale repair, ICP or Sim3.

## Frozen HELDOUT result

- All 53 frames rendered at 256x192; all NVS metrics finite; map parameter identity unchanged.
- NVS mean: PSNR `10.640901`, SSIM `0.336159`, LPIPS `0.559564`.
- Primary confidence>=1: coverage `0.800998572` (gate `>=0.95`, FAIL), AbsRel `0.133145676` (PASS), delta1 `0.811134506` (PASS), median ratio `0.963813007` (PASS), nonfinite `0` (PASS).
- Secondary confidence==2, report-only: coverage `0.801436203`, AbsRel `0.115710023`, delta1 `0.848198150`, median ratio `0.966152549`, nonfinite `0`.
- Failure attribution: coverage limitation, not a 10x/100x/1000x coordinate-scale failure. The frozen map is geometrically accurate where supported but does not cover enough of the M1 HELDOUT target pixels.
- Clearance, `epsilon_map_empirical`, and SAFER static G0: not run because Primary depth geometry is a prerequisite. No value is claimed.

## Counts and boundaries

```json
{
  "checkpoint": 0,
  "clearance": 0,
  "controller": 0,
  "download": 0,
  "environment_create": 0,
  "environment_modify": 0,
  "final_params": 1,
  "formal_completed": 1,
  "formal_process_attempts": 1,
  "formal_retry": 0,
  "frame_deletion": 0,
  "fresh_canonical_exports": 2,
  "g0_fresh_processes": 0,
  "heldout_depth_evaluations_completed": 1,
  "heldout_nvs_evaluations_completed": 1,
  "hyperparameter_sweep": 0,
  "icp_sim3_scale_repair": 0,
  "m2_or_variant": 0,
  "optimizer_steps": 21000,
  "runtime_patch": 1,
  "smoke_completed": 2,
  "smoke_process_attempts": 2
}
```

- GPU 1 was clean at finalization.
- The official SplaTAM checkout and original Conda environment were not modified.
- The persistent reverse-proxy watchdog and managed SSH tunnel were not modified or stopped.
- No result was rerun or selected post hoc; no M2, variant, sweep, deletion, ICP/Sim3/scale repair, opacity filter, controller benchmark, or checkpoint was created.
- The first HELDOUT launcher invocation stopped before reading HELDOUT because it referenced the wrong frozen manifest filename; its task-owned export directories were safely rebuilt and the same evaluator then completed. This was a non-semantic path wrapper repair, not a scientific retry.

## Artifacts

- Server task root: `/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1`
- Formal params remain only on authoritative storage: `/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1/outputs/ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1/params.npz`
- Map identity: none (failed maps are not published).
- Downstream handoff: `downstream_handoff.json`; selection: `selection.json`; manifest: `run_manifest.json`; validator: `validation_result.json`.
