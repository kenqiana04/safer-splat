# Replica Splatfacto SAFER-Native Baseline Qualification V1

## Result

`PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED`
Decision: `KEEP_SPLATFACTO_AS_NATIVE_COMPATIBILITY_BASELINE_NOT_NAVIGATION_MAP`
Only recommended next task: `REPLICA_GAUSSIAN_FRONTEND_FAILURE_DECOMPOSITION_AND_PROTOCOL_CONFORMANCE_AUDIT_V1`.

PR #56 evaluated SplaTAM and Gaussian-SLAM only; Splatfacto is an independent supplemental SAFER-native baseline because the frozen SAFER checkpoint and loader use Nerfstudio Splatfacto directly. The Replica V3 published complete-tree identity is `24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb`. PR #56 frozen pilot selection and ingestion-order identities passed. Official eval usage was zero.

The level-1 authority was the official SAFER Splatfacto config. Runtime metric dataparser validation used `orientation_method=none`, `center_method=none`, `auto_scale_poses=false`, scale 1 and identity transform. Direct c2w, intrinsics and pairwise-distance checks passed.

The 16/8 smoke completed technically, including checkpoint reload, unfiltered canonical export and native holdout rendering. Its geometry is explicitly diagnostic only and did not gate the 60/30 pilot. The one pilot completed with 1,396,211 Gaussians and unfiltered canonical export.

Pilot common-evaluator metrics were coverage 1.000000, AbsRel 0.603871, delta1 0.191574, and median ratio 0.666023. Coverage and finiteness passed, but the frozen geometry thresholds did not. This is a scientific negative result, not a rendering or loader failure.

SAFER native loader passed. Native and canonical static G0 each passed 256 fixed queries with three repeats; dual-path h/gradient/Hessian comparison passed. No navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, TUM work, full 270-frame training, depth supervision, pose optimization, Sim3, ICP or SplaTAM/Gaussian-SLAM reruns occurred.

PR #56's SplaTAM smoke is context only, not a fair pilot comparison; this task does not claim a winner. TUM remains frozen.

## Frozen inputs and runtime

The complete Replica V3 tree, selected-pilot registry, and ingestion order all matched their preregistered identities. The dataset adapter used only 16/8 smoke and 60/30 pilot train/holdout lists; no official-eval frame was available to either training dataloader. RGB files were source symlinks, while depth stayed exclusively in the frozen common evaluator.

The environment was `/disk1/zlab/conda_envs/splatnav/bin/python`: Python 3.8.20, PyTorch 2.1.2+cu118, CUDA 11.8, Nerfstudio 1.1.5 and gsplat 1.4.0. The authority was level 1: the official SAFER Splatfacto `config.yml` (SHA-256 `7e83fb0711a1decc55518e66e43a34395188c2e2a2de0e5ec24d6bb510fb7b8d`), with all model, loss, learning-rate, densification and culling parameters retained. The sole operational repair was a task-owned CUDA-11.8 gsplat JIT cache for the existing Python 3.8 environment; it changed no installed package or model semantics.

## Metric-pose contract

The actual `NerfstudioDataParserConfig` used no orienting, centering or auto-scaling. Runtime `dataparser_transform` was identity and `dataparser_scale` was 1.0. Source-to-runtime c2w error, intrinsic error and pairwise translation-ratio error were all zero; reprojection and metric-depth roundtrip met the frozen bounds. Camera optimizer and pose update were disabled, as were spatial contraction, COLMAP and depth supervision.

## Smoke operational result

The 16-frame smoke ran 2,000 iterations with seed 20260728 and completed in 71.9 seconds. It saved and reloaded `step-000001999.ckpt`, exported 181,380 unfiltered Gaussians, and rendered all eight holdouts with finite native RGB/depth. The common-renderer diagnostic was coverage 1.000000, AbsRel 0.613054, delta1 0.177905 and median depth ratio 0.757779. Those values are reported only: the corrected protocol explicitly forbids using smoke geometry to block the pilot.

## Qualification-pilot geometry and map structure

The single 60-frame, 30,000-iteration pilot completed and exported 1,396,211 unfiltered Gaussians. The common evaluator reported coverage 1.000000, AbsRel 0.603871, SqRel 0.997368, RMSE 1.572712, RMSE-log 0.935318, delta1 0.191574, delta2 0.369070, delta3 0.521820, median ratio 0.666023, PSNR 18.194419 and SSIM 0.520898. Thus the coverage and finite-prediction requirements passed, but AbsRel, delta1 and ratio did not meet the pilot qualification gate.

The map was finite and in the unchanged metric frame, but its scale audit recorded a 1.76e-09 m minimum scale, 78.81 m maximum scale, and a median depth ratio outside `[0.80, 1.25]`. No visual impression is used as a scale certificate; the geometry gate remains failed.

## SAFER static compatibility

The frozen SAFER head `f63b4c496861c4f8881348d74244c1ff9a528d51` and required source blobs matched. The native loader loaded exactly 1,396,211 Gaussians from the pilot checkpoint; its means, exponentiated scales, normalized WXYZ quaternions and sigmoid opacities matched the canonical export. Native and canonical G0 each performed three static passes over the same 256 points at radius 0.015 m. Both were finite, repeatable and Hessian-symmetric; cross-path maximum absolute differences were h=2.38e-06, gradient=1.91e-06 and Hessian=3.34e-06, within the frozen tolerances.

## Boundaries and interpretation

The task ran neither full 270-frame training nor navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C or any TUM rollout. It used no Sim(3), ICP, scale fitting, hyperparameter search, SplaTAM rerun or Gaussian-SLAM rerun. The result therefore establishes native static compatibility only. It does not establish pilot geometry qualification, navigation-map suitability, or superiority over PR #56 frontends.
