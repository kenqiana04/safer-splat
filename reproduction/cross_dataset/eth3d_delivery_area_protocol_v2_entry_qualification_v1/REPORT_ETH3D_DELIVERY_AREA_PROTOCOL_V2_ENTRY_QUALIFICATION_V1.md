# REPORT — ETH3D Delivery Area Protocol V2 Entry Qualification V1

## Answer first

**PASS_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION**

**AUTHORIZE_BOUNDED_ETH3D_DELIVERY_AREA_ASSET_ACQUISITION_AND_CONTRACT_AUDIT**

ETH3D Delivery Area has a metadata-level, leakage-controlled entry path for one future GT-pose RGB-only map-only learned Gaussian map. The selected future mapping input is the low-resolution 4-camera rig's undistorted RGB and official COLMAP calibration; all DSLR images remain cross-view evaluation. The selected frontend is the official 3DGS implementation at frozen commit `54c035f7834b564019656c3e3fcc3646292f727d`. Official rendered depth is laser-scan-derived ground truth and is prohibited as mapping input, so the SplaTAM RGB-D route is rejected.

This PASS authorizes only the next bounded asset acquisition and contract audit. **Training remains unauthorized.** No dataset archive body, image, depth map, scan, occlusion payload, environment, model, map, route, controller, or final split was created.

## 1. PR #76 and Protocol V2 identity

- PR #76 lineage head: `d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de`; open, draft, unmerged, mergeable, and preserved.
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`.
- New-dataset checklist SHA-256: `7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593`.
- PR #76 report SHA-256: `052ccdf0b63fbfdfed49a0a5f861a9f0f8bbf7e337079805cfa382cf5153b570`.
- PR #76 run manifest SHA-256: `a80e3f09a902934b595accdc1726298a2695abbb312009bb2290002e5aa4b97f`.

## 2. ETH3D official authority

Twelve frozen primary-authority entries cover the official ETH3D home, MVS overview/datasets/documentation, SLAM overview/datasets/documentation, the official paper HEAD, and four official repositories. Each web snapshot records final URL, retrieval UTC, status, SHA-256, title, and cited fields. GitHub identities record default branch, HEAD, license SHA, and submodule commits.

| Official repository | Default branch | Frozen HEAD | License SHA-256 | Submodules |
|---|---:|---|---|---:|
| [ETH3D/dataset-pipeline](https://github.com/ETH3D/dataset-pipeline) | `master` | `e09275b39b30c9c59abf535b849fcc539dc03efd` | `1123317c18bb917830bf070fdf00cf02f149ca3035e50c5e7bed16a7ab84512a` | 0 |
| [ETH3D/multi-view-evaluation](https://github.com/ETH3D/multi-view-evaluation) | `master` | `0daa4f4de036d47d37a6ba054c51fd66642ef896` | `0bb885021d51235d54e7fd7dfb9377a9381ff9874bff4647396921c347dc33a7` | 0 |
| [ETH3D/format-loader](https://github.com/ETH3D/format-loader) | `master` | `04b0cb379945880a9b4aa20fed5f593a6ada9f4e` | `db53517e98f6a93e04674031dc27c1fab3bd2e8fb0b2fe0f087fd07c0bb77c3a` | 0 |
| [graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting) | `main` | `54c035f7834b564019656c3e3fcc3646292f727d` | `c5ba70a2194af2aefe85dfe3da68608dcb3abd21a3aa53b55aa297c2f0b60eb3` | 4 |

Primary pages: [ETH3D home](https://www.eth3d.net/), [MVS overview](https://www.eth3d.net/overview), [datasets](https://www.eth3d.net/datasets), [documentation](https://www.eth3d.net/documentation), [SLAM overview](https://www.eth3d.net/slam_overview), and the [official MVS paper](https://www.eth3d.net/data/schoeps2017cvpr.pdf).

## 3. Delivery Area benchmark identity

`delivery_area` is a **training scene in the ETH3D Multi-View Stereo / 3D reconstruction benchmark**. It is not an ETH3D SLAM RGB-D sequence. The official MVS pages list it in both high-res and low-res many-view training sections, while the separate SLAM pages define visual-inertial, stereo, and RGB-D sequences recorded for a different benchmark.

## 4. High-res and low-res assets

- High-res DSLR: indoor, 44 images, undistorted JPEG, official COLMAP text intrinsics/extrinsics/triangulated image-only points, plus raw/clean/eval scans, occlusion data, and rendered depth.
- Low-res rig: indoor, 4 × 237 = 948 PNG images, four synchronized cameras per capture, official fixed-rig/COLMAP calibration and poses, plus the same reference families and stereo-pair GT.

| Official archive | Variant | Declared size | HEAD Content-Length | Frozen role |
|---|---|---:|---:|---|
| `delivery_area_dslr_undistorted.7z` | HIGH_RES_DSLR | 0.5 GB | 478076254 | CROSS_VIEW_EVALUATION_ONLY |
| `delivery_area_dslr_jpg.7z` | HIGH_RES_DSLR | 0.4 GB | 372958192 | NOT_REQUIRED |
| `delivery_area_dslr_raw.7z` | HIGH_RES_DSLR | 1.1 GB | 1179816961 | NOT_REQUIRED |
| `delivery_area_scan_raw.7z` | SHARED_REFERENCE | 0.4 GB | 398284446 | OPTIONAL_DIAGNOSTIC_ONLY |
| `delivery_area_scan_clean.7z` | SHARED_REFERENCE | 0.4 GB | 381363091 | REFERENCE_ORACLE_ONLY |
| `delivery_area_dslr_scan_eval.7z` | HIGH_RES_DSLR | 0.1 GB | 122553428 | CROSS_VIEW_EVALUATION_ONLY |
| `delivery_area_dslr_occlusion.7z` | HIGH_RES_DSLR | 0.1 GB | 56850384 | CROSS_VIEW_EVALUATION_ONLY |
| `delivery_area_dslr_depth.7z` | HIGH_RES_DSLR | 0.4 GB | 388144128 | CROSS_VIEW_EVALUATION_ONLY |
| `delivery_area_rig_undistorted.7z` | LOW_RES_RIG | 0.3 GB | 278900786 | MAPPING_INPUT_ONLY |
| `delivery_area_rig.7z` | LOW_RES_RIG | 0.3 GB | 316556364 | NOT_REQUIRED |
| `delivery_area_rig_scan_eval.7z` | LOW_RES_RIG | 0.1 GB | 36142207 | HELDOUT_EVALUATION_ONLY |
| `delivery_area_rig_occlusion.7z` | LOW_RES_RIG | 0.1 GB | 56643980 | HELDOUT_EVALUATION_ONLY |
| `delivery_area_rig_depth.7z` | LOW_RES_RIG | 0.6 GB | 636547888 | HELDOUT_EVALUATION_ONLY |
| `delivery_area_rig_stereo_pairs_gt.7z` | LOW_RES_RIG | 0.9 GB | 957171745 | PROHIBITED_AS_MAPPING_INPUT |

All 14 unique archive URLs returned HTTP 200 to HEAD with `application/x-7z-compressed`; response-body bytes were zero.

## 5. Why this is not ETH3D SLAM RGB-D

The MVS overview explicitly defines DSLR and synchronized multi-camera-rig reconstruction challenges with laser-scan ground truth. The SLAM overview separately defines motion-capture/SfM-ground-truthed sequences usable for VI, stereo, and RGB-D SLAM. A shared institution and a generic scene label do not merge those benchmark families.

## 6. License

PASS_NONCOMMERCIAL_ACADEMIC_COMPATIBILITY. ETH3D data are CC BY-NC-SA 4.0; the official 3DGS code is research/evaluation and non-commercial only. Local academic processing and compact derived statistics/figures are allowed with attribution. Raw payload is excluded from Git. A distributed trained map must conservatively remain non-commercial, carry CC BY-NC-SA 4.0 and ETH3D attribution/change/citation notices, and preserve applicable 3DGS notices; broader use needs separate permission or legal review.

## 7. Input/reference/oracle isolation

Only undistorted TRAIN RGB, official intrinsics/poses, validated non-reference masks, and rig grouping may enter `TRAIN_INPUT_ROOT`. `EVAL_ORACLE_ROOT` contains held-out RGB, depth, scan, scan_eval, and occlusion assets and is unreadable by training. A future open-file audit must prove zero held-out/reference access. Reference-based split choice, pruning, or scale repair is prohibited.

## 8. Is rendered depth ground truth?

Yes. Official documentation and `ETH3D/dataset-pipeline` show `GroundTruthCreator` rendering depth from aligned laser scans plus occlusion mesh/splats. It is evaluation ground truth, not independent sensor RGB-D.

## 9. Is the SplaTAM route allowed?

No: `NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE`. No primary source establishes independent synchronized sensor RGB-D for this MVS scene. Using the supplied rendered depth would leak reference geometry into mapping.

## 10. Official 3DGS compatibility

Metadata-level compatibility passes. ETH3D undistorted calibration is PINHOLE COLMAP text and supplies image-only triangulated points. The frozen official 3DGS loader accepts text or binary cameras/images/points3D and PINHOLE/SIMPLE_PINHOLE cameras. Therefore directory adaptation can avoid feature matching and SfM reruns. Future asset validation must still prove exact paths, scale/frame, no depth argument, canonical export, deterministic runtime, 24 GB GPU fit, and task-owned environment build.

## 11. Splatfacto historical boundary

Splatfacto is a compatibility reference only. Prior TUM/Replica geometry failures and easier export do not justify choosing it. It cannot be run in parallel and selected after results; any later use requires a separate protocol.

## 12. Selected frontend

`OFFICIAL_3DGS_COLMAP_RGB_ONLY`. Current official default iterations are 30,000; no run is authorized here. Depth input is frozen empty. Exported xyz/scales/normalized rotations/opacity/SH can support a future canonical ellipsoid adapter, but parity remains a later qualification gate.

## 13. Selected modality

`LOW_RES_MANY_VIEW_RIG_RGB_ONLY`, selected solely for more official views, capture grouping, and preservation of a distinct DSLR cross-view channel—not on trained performance.

## 14. DSLR cross-view role

`HIGH_RES_DSLR_RGB_ONLY` is `CROSS_VIEW_EVALUATION_ONLY`. No DSLR RGB enters TRAIN if the rig route is used.

## 15. Split generation rule

Status: `FUTURE_SPLIT_CONTRACT_FEASIBLE_NOT_GENERATED`. The unit is `RIG_CAPTURE_GROUP`; all four simultaneous camera images stay in the same partition. A later asset audit must construct and sensitivity-check deterministic spatial group splits, then freeze one before training. No final split and no universal 80/20 ratio were created here.

## 16. Reference authority

Status: `REFERENCE_AUTHORITY_ENTRY_PATH_FEASIBLE_PENDING_ASSET_AUDIT`. `A_DENSE_INDEPENDENT_GEOMETRY` is provisional only. R-axis evaluation uses variant scan_eval + official evaluator + occlusion. Rendered depth is observable-ray evaluation only. Route/collision use of scan_clean/alignment/occlusion is only a candidate until asset-level completeness, frame, floor, thin-object, and queryability checks pass.

## 17. scan_eval versus scan_clean

`scan_eval` is tailored to MVS evaluation and excludes/supports geometry according to multi-view observability; the official pipeline/paper note the at-least-two-image condition. `scan_clean` is the cleaned aligned laser scan and is the better route-oracle candidate, but is not automatically complete or routeable. Neither is mapping input.

## 18. UNKNOWN contract

`UNKNOWN_CONTRACT_FEASIBLE_FOR_FUTURE_ASSET_VALIDATION`. UNKNOWN is never free. U1 frustum support, U2 multi-view free rays truncated before a learned first surface, and U3 learned-Gaussian visibility counts are entry-feasible candidates. Absence/low alpha/frustum membership alone cannot establish free space. The later algorithm must be frozen before mapping, use no reference at runtime, require conservative multi-view support, return UNKNOWN to SAFER, and permit unknown-as-occupied.

## 19. Route contract

`INDEPENDENT_REFERENCE_ROUTE_PATH_FEASIBLE_PENDING_ASSET_AUDIT`. A route may be generated only from verified reference geometry and robot geometry before training, with no candidate-map access, route deletion, or camera-path substitution. It must cover predeclared clearance strata and remain within verified reference/known support.

## 20. Robot contract

`REAL_WORLD_SCENE_MAP_WITH_ORACLE_STATE_SIMULATED_NAVIGATION` only. The 6D double-integrator, Euler `dt=0.05 s`, 0.10 m sphere, 0.01 m base margin, componentwise 0.10 m/s and 0.10 m/s² limits, bounded QP, and swept-sphere oracle are project benchmark choices—not ETH3D facts and not a real-robot safety claim.

## 21. Physical budget

`PHYSICAL_BUDGET_DERIVATION_PATH_FEASIBLE`. The later inequality is `UpperBound[e_plus | route tube] <= B_map_available`, where clearance is reduced by localization, shape, sampled-data, stopping, and tracking terms. `epsilon_loc=0` is allowed only for oracle-state simulation. No arbitrary centimetre gate or closed numeric budget is claimed.

## 22. Future evaluator

`PROTOCOL_V2_FUTURE_EVALUATOR_PATH_FEASIBLE`. It freezes integrity/no-leakage, native/common parity, the 11-point alpha grid, official multi-tolerance accuracy/completeness/F-score/visibility reporting, navigation-conditioned UNKNOWN/route/e_plus/budget/oracle evidence, separate G0, and descriptive rig-heldout/DSLR-cross-view NVS. There is no universal numeric hard gate.

## 23. Minimal future download whitelist

Exactly nine archives are authorized only in the next task:

| Archive | Declared | Exact HEAD bytes | Role | Physical root |
|---|---:|---:|---|---|
| `delivery_area_rig_undistorted.7z` | 0.3 GB | 278900786 | MAPPING_INPUT_ONLY | TRAIN_INPUT_ROOT |
| `delivery_area_rig_scan_eval.7z` | 0.1 GB | 36142207 | HELDOUT_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_rig_occlusion.7z` | 0.1 GB | 56643980 | HELDOUT_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_rig_depth.7z` | 0.6 GB | 636547888 | HELDOUT_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_scan_clean.7z` | 0.4 GB | 381363091 | REFERENCE_ORACLE_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_dslr_undistorted.7z` | 0.5 GB | 478076254 | CROSS_VIEW_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_dslr_scan_eval.7z` | 0.1 GB | 122553428 | CROSS_VIEW_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_dslr_occlusion.7z` | 0.1 GB | 56850384 | CROSS_VIEW_EVALUATION_ONLY | EVAL_ORACLE_ROOT |
| `delivery_area_dslr_depth.7z` | 0.4 GB | 388144128 | CROSS_VIEW_EVALUATION_ONLY | EVAL_ORACLE_ROOT |

Compressed total from HEAD: `2435222146` bytes.

## 24. Denylist

| Archive | Reason |
|---|---|
| `delivery_area_scan_raw.7z` | not needed for the minimum Protocol V2 path |
| `delivery_area_dslr_raw.7z` | not needed for the minimum Protocol V2 path |
| `delivery_area_dslr_jpg.7z` | not needed for the minimum Protocol V2 path |
| `delivery_area_rig.7z` | not needed for the minimum Protocol V2 path |
| `delivery_area_rig_stereo_pairs_gt.7z` | two-view ground-truth disparity is prohibited as mapping input |

## 25. Future disk budget

The exact compressed whitelist total is `2435222146` bytes. Content-class expansion estimates total `7916846285` bytes; these are project planning estimates pending archive listings. Reserve 30 GB decimal for acquisition, extraction, conversion, evaluator work, and later output headroom. The current metadata-only task is capped at 1 GiB and contains zero dataset bytes.

## 26. Training authorization

`training_authorized=false`. Entry cannot jump to training. Required order: bounded acquisition → asset/split/reference audit → UNKNOWN/route/budget freeze → official 3DGS environment qualification → smoke → one frozen formal mapping → Protocol V2 qualification.

## 27. Allowed and forbidden claims

Allowed: only a metadata-level possible GT-pose RGB-only map-only route and next-task bounded acquisition. Forbidden: qualified map, navigation, full SLAM/tracking, sensor RGB-D, real-robot safety, solved UNKNOWN/route/budget, successful 3DGS runtime, any R/N grade, or authorized training.

## 28. Execution counts

| Counter | Value |
|---|---:|
| `official_html_fetch_count` | 14 |
| `github_api_metadata_fetch_count` | 13 |
| `small_official_text_fetch_count` | 13 |
| `official_paper_head_count` | 2 |
| `dataset_archive_download_count` | 0 |
| `dataset_payload_bytes` | 0 |
| `controlled_official_html_fetch_count` | 14 |
| `controlled_github_api_metadata_attempt_count` | 13 |
| `controlled_github_api_metadata_success_count` | 12 |
| `controlled_small_official_text_fetch_count` | 13 |
| `controlled_official_paper_head_count` | 2 |
| `archive_http_head_count` | 14 |
| `other_http_head_count` | 4 |
| `total_http_head_count` | 18 |
| `interactive_browser_official_page_fetch_count` | 8 |
| `interactive_browser_archive_link_resolution_attempt_count` | 6 |
| `interactive_browser_archive_response_body_bytes` | 0 |
| `http_head_count` | 14 |
| `image_download_count` | 0 |
| `depth_download_count` | 0 |
| `scan_download_count` | 0 |
| `occlusion_download_count` | 0 |
| `model_download_count` | 0 |
| `git_clone_count` | 0 |
| `environment_create_count` | 0 |
| `environment_modify_count` | 0 |
| `training_count` | 0 |
| `optimizer_count` | 0 |
| `model_count` | 0 |
| `map_count` | 0 |
| `controller_count` | 0 |
| `planner_count` | 0 |
| `route_generation_count` | 0 |
| `final_data_split_generation_count` | 0 |
| `asset_whitelist_count` | 9 |
| `asset_denylist_count` | 5 |

All dataset/archive/payload/image/depth/scan/occlusion/model downloads; clones; environment creates/modifies; training/optimizer/model/map/controller/planner/route/final-split executions are zero.

## 29. FINAL_STATUS

`PASS_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION`

## 30. FINAL_DECISION

`AUTHORIZE_BOUNDED_ETH3D_DELIVERY_AREA_ASSET_ACQUISITION_AND_CONTRACT_AUDIT`

## 31. Only next task

`ACQUIRE_ETH3D_DELIVERY_AREA_FROZEN_ASSETS_AND_VALIDATE_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT_V1`

That next task may acquire only the nine frozen archives and must finish the 27 post-download checks before any environment, smoke, or training task is authorized.
