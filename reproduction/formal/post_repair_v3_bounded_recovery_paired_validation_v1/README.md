# Post-Repair V3 Bounded Recovery Paired Validation V1

This directory freezes a prospective formal85 protocol. The Stonehenge 85-trial benchmark is repeatedly exposed and is not a pristine holdout. Bounded recovery, candidate order, geometry, dynamics, Reference evidence, statistical gate, and boundary handling are frozen before execution. No cross-scene, physical-world safety, hard-real-time, or deployment claim follows from this protocol.

The primary comparison is bounded-recovery Active versus the immutable frozen Reference. The old repaired-Active result remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE` and is used only for secondary diagnostics. The two primary gates are exact represented-map hard safety at radius `0.015 q` and progress non-inferiority with 10,000 paired percentile resamples, seed `20260911`, margin `-0.02`, and strict `lower95 > -0.02`. No clipping, tuning, trial exclusion, or boundary imputation is allowed.

A valid typed assurance boundary is a complete paired trial. Progress uses the last actually committed state, and hard safety audits only executed segments. A result root that already exists must never be relaunched; `BATCH_STOP` preserves evidence for diagnosis and does not authorize automatic retry.

Attempt0 is immutable at `/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_20260920`. It stopped before the child runtime because the runner referenced a non-existent lock basename. Retry1 uses the canonical `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json`; no compatibility copy or symlink exists under the wrong basename.

Future launch, from the worktree root only:

```bash
/disk1/zlab/conda_envs/safer_splat_official/bin/python reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/launch_post_repair_v3_bounded_recovery_paired_validation_v1.py --launch --authorize-execution EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_R1
```

Future Retry1 result root: `/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_retry1_20260920`

Future Retry1 tmux: `post_repair_v3_bounded_recovery_paired_validation_v1_retry1`

Compact percentage monitor:

```bash
/disk1/zlab/conda_envs/safer_splat_official/bin/python reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py
```

Use `--json` for machine-readable output or `--all-trials` to expand all trials.

After 85/85 immutable locks and `BATCH_COMPLETE`, run the analyzer from the worktree root:

```bash
CUDA_VISIBLE_DEVICES=1 /disk1/zlab/conda_envs/safer_splat_official/bin/python reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/analyze_post_repair_v3_bounded_recovery_paired_validation_v1.py --post-collection-authorized
```

The launcher never invokes the analyzer and never reruns the Reference.
