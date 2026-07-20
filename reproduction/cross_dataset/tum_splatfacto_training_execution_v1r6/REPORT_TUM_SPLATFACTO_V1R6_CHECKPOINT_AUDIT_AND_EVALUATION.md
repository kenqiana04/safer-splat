# TUM Splatfacto V1R6 Checkpoint Audit, Evaluation, Render, and G0 Candidate Registration

## Result

`PASS_FORMAL_TUM_V1R6_CHECKPOINT_AUDIT_AND_EVALUATION_COMPLETE`

## V1R6 identity and completed formal attempt

- Run label / seed / timestamp / experiment: `V1R6` / `20260716` / `20260717_070309` / `tum_fr1_room_splatfacto_v1r6`.
- Run root: `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309`.
- Execution record root: `/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r6_seed20260716_20260717_070309`.
- The single formal attempt exited `0`, reached final step `29999`, and used neither resume nor retry. This audit did not invoke `ns-train`, `Trainer.train`, or `train_iteration`.

## Frozen checkpoint, config, data, and runtime

- Final checkpoint: `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/nerfstudio_models/step-000029999.ckpt`.
- Checkpoint identity: `491777938` bytes (`468.996` MiB), SHA-256 `4941bf1faba1aed31949ee4114898c0eec33ff1a46b7bcadad6d06f5f647ae6b`, readable regular file, mode `0664`, no symlink, and no hard-link multiplicity.
- CPU read-only `torch.load` resolved step `29999`; it found 45 tensors (45 floating), with zero non-finite tensors.
- Config: `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml`, SHA-256 `c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe`.
- Frozen config contract passed: Splatfacto; seed `20260716`; 30,000 iterations; save/image/all-image intervals `2000`/`100`/`1000`; no mixed precision or grad scaler; camera optimizer off; TUM `freiburg1_room`; orientation/center none; no pose auto-scale; downscale 1; fraction split 0.8; depth scale 0.0002.
- Transforms SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Fraction manifest reconstructed with Nerfstudio's `get_train_eval_split_fraction`: 300 total, 240 train, 60 test/eval, 0 dropped.
- Runtime used physical GPU 1 as logical `cuda:0`, PyTorch `2.1.2+cu118`, CUDA `11.8`, the precompiled gsplat `1.4.0+pt21cu118` overlay, and the setuptools/pkg_resources overlay. `_backend._C` was non-null and exposed `CameraModelType`; gsplat wheel SHA-256 was `954e0a19ed5c84f27bd58581c24edd3c0b1b82bfd13510f9951b30f2606682d2`.

## Formal test evaluation and RGB render

- Evaluation command: `ns-eval --load-config <RUN_ROOT>/config.yml --output-path <AUDIT_ROOT>/formal_eval/metrics.json`; exit code `0`.
- It completed the fixed 60-frame test/eval split. Metrics JSON SHA-256: `6acb8e3d9599f0245b6bd82cdc541264d8379203db727179ad3f1883d8d2ff43`.
- Metrics: PSNR `9.436382293701172` (std `1.9206037521362305`), SSIM `0.3585314154624939` (std `0.0989714190363884`), LPIPS `0.7240599393844604` (std `0.08114152401685715`), rays/s `31352056.0` (std `5098923.5`), FPS `102.05747985839844` (std `16.598058700561523`). Every numeric scalar was finite.
- Render command: `ns-render dataset --load-config <RUN_ROOT>/config.yml --output-path <AUDIT_ROOT>/formal_render --image-format png --rendered-output-names rgb --split test`; exit code `0`.
- Render produced exactly 60 RGB-only test frames at consistent `640x480 RGB`; every file was readable, non-empty, and non-zero. The server-side RGB manifest is `manifests/render_rgb_manifest.csv`, SHA-256 `dc99c3e1488553be47e7be9648026882220c12336e97fe022bb3ca9dab83169c`.

## Immutability and safety boundaries

- After evaluation/render, final checkpoint, config, transforms, and the original training log were unchanged.
- A post-evaluation `/proc` scan found no training-related process. GPU 1 reported `0%` utilization, `6 MiB` used, and no compute process.
- No new training, resume, retry, checkpoint rewrite, SAFER, navigation, or G1 was run. Evaluation and render output remained under the task-owned audit root, not the formal run root.

## G0 candidate and separate authorization boundary

`tum_fr1_room_splatfacto_v1r6_seed20260716_20260717_070309` is registered as `TUM_G0_CHECKPOINT_CANDIDATE_READY_FOR_SEPARATE_DOWNSTREAM_AUTHORIZATION`. It is a candidate only: any downstream SAFER or navigation evaluation still needs separate user authorization; G1 remains prohibited.

## Evidence closure

- Server evidence root: `/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r6_seed20260716_20260717_070309/checkpoint_audit_and_evaluation`.
- Compact tracked evidence contains the checkpoint/config/content audits, runtime identity, metrics and render summaries, immutability record, G0 candidate, handoff, and validator.
- Validator status: `PASS_FORMAL_TUM_V1R6_CHECKPOINT_AUDIT_AND_EVALUATION_COMPLETE`; unresolved critical fields: `[]`.
