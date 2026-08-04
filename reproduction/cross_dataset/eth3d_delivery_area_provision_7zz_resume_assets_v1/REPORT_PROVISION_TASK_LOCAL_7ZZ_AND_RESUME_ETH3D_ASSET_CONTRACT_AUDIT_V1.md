# Report: Provision task-local 7zz and resume ETH3D asset contract audit V1

## Outcome

- FINAL_STATUS: `NO_ETH3D_DELIVERY_AREA_REFERENCE_ROUTE_BENCHMARK_CONTRACT`
- FINAL_DECISION: `CLOSE_ETH3D_DELIVERY_AREA_BEFORE_ENVIRONMENT_OR_TRAINING`
- training_authorized: `false`
- unresolved critical evidence: none
- Only next task: `REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_ALTERNATIVES_V1`

All asset, integrity, split, isolation, coordinate, continuous-reference, ideal UNKNOWN,
robot, and physical-budget prerequisites passed. The task closes fail-closed because the
frozen planner-coupled route composition requires at least 50% blocked straight lines,
while the corrected deterministic free-3D reference-only PRM candidate set produced
0/89054 = 0.000000. No threshold or frozen contract
was changed, and no route registry was frozen.

## Lineage and infrastructure

- Branch: `eth3d-delivery-area-provision-7zz-resume-assets-v1`
- Base/head: `eth3d-delivery-area-frozen-assets-contract-audit-v1` / `84126353999dc6af979f4d8533a5cbaf638895be`
- PR #78 blocker preserved: true; blocker SHA-256 `75f16f176ff887bb1b71f2d7e0d02e3663aa9ac72df85dc9b8c23df1d965eff5`
- PR #77 head: `aea42e4ec9baea5b7d4843b155b02c74a242a56b`
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`
- 7zz route/version/SHA: `T1_TASK_LOCAL_OFFICIAL_PORTABLE_7ZZ` / `7-Zip (z) 26.02 (x64) : Copyright (c) 1999-2026 Igor Pavlov : 2026-06-25` / `1676a968815b92e865bc0ffeecee3fa284ba4402bf23dc2bec2412c4b502e922`
- 7zz provenance: `https://github.com/ip7z/7zip/releases/download/26.02/7z2602-linux-x64.tar.xz`; system/environment impact: none
- Managed SSH/proxy repair attempts: 0; final proxy reachable: `True`
- Watchdog: `Running` (`SCHED_S_TASK_RUNNING`);
  established SSH sessions preserved: 2; SSH/network/firewall changes: 0/0/0
- Operational autonomy actions: 15; task-owned process terminations: 16; scientific changes: 0

## Assets

- Official downloads: 9; compressed bytes: 2435222146; denylist: 0
- Extracted files/bytes: 2940/7871830169
- CRC/security/quarantine: PASS/PASS/PASS
- `delivery_area_rig_undistorted.7z`: 278900786 bytes, SHA-256 `fa71d95e43e0357c62b3ee1ca3629dc1c9c9ce1c2bd97927fc4cf54ab33249fa`, CRC PASS, tree SHA-256 `c2e83b473aafb0b9d7360604a6a769a4ced7ce4fd7e4add3a771209091354162`
- `delivery_area_rig_scan_eval.7z`: 36142207 bytes, SHA-256 `140f066e9b4e66fc6b23279c02ec28342f24cbcc95c246afa29a21129f10f516`, CRC PASS, tree SHA-256 `dc21a090df75053c10dc3a298f2dc731f39d2a4e864603569eb6792bfff8c8d9`
- `delivery_area_rig_occlusion.7z`: 56643980 bytes, SHA-256 `2fd77822edf2f3f1ff69cddbc265a772f3dc0dfa1b1a0fd62805355ca920a43b`, CRC PASS, tree SHA-256 `b361f2e72852c4e6dbd49852d221b4a99ab0ed517939543811a03938d0558f5f`
- `delivery_area_rig_depth.7z`: 636547888 bytes, SHA-256 `6a367fa44bba34f44bd074f2a37b178df5ca037d6c162afe34d027f0ffce7841`, CRC PASS, tree SHA-256 `e7ae1e0a7fcfebc60d39c979b3962d9335a4e3f4a0a69828102485b806c932c9`
- `delivery_area_scan_clean.7z`: 381363091 bytes, SHA-256 `cd3f41c563911fcc630241f04bd2e0ac5e9e0091bb298c2a74873f3dca837436`, CRC PASS, tree SHA-256 `2982ba8b381e2abf633db9b82b297049e83c27ff37e354c61110afb980e07849`
- `delivery_area_dslr_undistorted.7z`: 478076254 bytes, SHA-256 `9acf5efec4b99a69b89ebb87b403259730756c1a510307c92e5f2ce2d22658f3`, CRC PASS, tree SHA-256 `b1756248a4df184532c39e87a9bed79a072ac9177cd13db937c23c3fb7b6d733`
- `delivery_area_dslr_scan_eval.7z`: 122553428 bytes, SHA-256 `8e07f7a7956a41c1ecc18ca8a61d3fff274c080050301a1b7dff12a3ca5ed5d2`, CRC PASS, tree SHA-256 `0c688bb21e0a0be894c8119feb927e6e967725c4ea3b885d4922a13c398490fa`
- `delivery_area_dslr_occlusion.7z`: 56850384 bytes, SHA-256 `f61a1bd74bc8fe07d03973520cc1433ea99566fcd637a654a5b2072d475a1b4c`, CRC PASS, tree SHA-256 `69d766db27a31f52e66100a97b6a6dfe076370e6b312b934895deca004903756`
- `delivery_area_dslr_depth.7z`: 388144128 bytes, SHA-256 `e6edc65b5b6de343876382040c839405eef79abed33319aa377883f4ddc5775a`, CRC PASS, tree SHA-256 `7ee564b1abb56c6590ac4a7be2fd8b0a0e1a806a190457307638f05d2506383f`

## Rig, split, and isolation

- Modality: `LOW_RES_MANY_VIEW_RIG_RGB_ONLY`; fallback false
- Rig RGB/groups/cameras: 948/237/4; DSLR: 44
- Sparse points: `OFFICIAL_COLMAP_IMAGE_TRIANGULATION_WITH_IMAGE_TRACKS`; no laser scan, ICP, Sim(3), or scale repair
- TRAIN/HELDOUT/GUARD: 187/48/2; split SHA `dc6729a60e0f2971cb671e30bcce3a04adcd8f99298395d42f21855d666cc435`; 3 fresh processes PASS
- Train-only COLMAP: 748 images, 40092 points, SHA `5b0002cbdd4dff8985574c8f5d61640e9535709634959327e3b705794830b478`; 3 fresh builds PASS
- TRAIN reference/heldout access: 0/false; new triangulation/reference injection: 0/0

## Coordinate, reference, UNKNOWN, and physical contract

- Metric coordinate/depth/alignment: `PASS_ETH3D_METRIC_COORDINATE_CONTRACT`; no fitted transform
- Continuous reference: 2434103 vertices, 4868354 faces, SHA `82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370`
- Independent distance parity: 0.0 m <= 1e-06 m
- UNKNOWN: `ETH3D_MULTI_VIEW_FIRST_SURFACE_UNKNOWN_V1`, 3 groups / 15 deg / 0.01 m; 512 qualified nodes
- Robot: free-3D sphere r=0.1 m, exact swept segment, bounded QP
- Reaction-stop/non-map reserve: 0.09526279441628825 / 0.23526279441628825 m

## Route failure evidence

- Corrected candidate dimensionality: `THREE_DIMENSIONAL_FREE_3D_ROBOT_CONTRACT`
- Qualified PRM nodes/edges: 512/3542
- Cost: `edge_length_plus_inverse_reference_residual_budget`
- Valid path candidates: 89054; blocked straight-line candidates: 0; ratio: 0.0
- Required ratio: 0.5; frozen route count: 0; route registry SHA: none
- Exact swept-sphere collision predicate: true; candidate map access: 0
- Larger-than-cap distances are conservative lower bounds; uncapped distance claimed: false
- Three-process registry reproduction was not continued after the deterministic composition gate failed.

## Future evaluator and no-execution boundary

The future evaluator remains frozen and unexecuted. GPU 1: `1, NVIDIA GeForce RTX 4090, GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d, 24564 MiB, 6 MiB, 0 %`.
GPU compute processes: `none`.
Task-owned running processes: 0.
Environment create/modify, official 3DGS, training, optimizer, smoke, map, controller,
planner benchmark, candidate-map access, ICP/Sim(3), scale repair, and frame deletion are all zero.

Server report: `/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1/REPORT_PROVISION_TASK_LOCAL_7ZZ_AND_RESUME_ETH3D_ASSET_CONTRACT_AUDIT_V1.md`
No environment handoff is issued in Case C.
