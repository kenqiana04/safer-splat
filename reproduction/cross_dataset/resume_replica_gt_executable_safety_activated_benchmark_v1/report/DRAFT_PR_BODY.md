## Outcome

`FINAL_STATUS=PASS_ACTIVATED_MECHANISM_WITH_LOW_REPRESENTATIVE_PREVALENCE`

`FINAL_DECISION=DO_NOT_FRAME_CORE_V1_AS_BROAD_REAL_TIME_REPLACEMENT_FOR_SAFER`

`ONLY_NEXT_TASK=DECIDE_BETWEEN_FAST_GAUSSIAN_SWEPT_CERTIFICATE_AND_BACKUP_SET_RESEARCH_V1`

## Frozen scope

- Preserves PR #84 `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`, PR #85 `7afef38392bec36d9d9811e5a22c816da5faf1ff`, and PR #86 `d4f20f44a810afc2d6379853a286a3e18b175221`.
- Reproduces the exact nested B0-B3 method matrix and library `3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe`.
- Uses map `3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55` and reference mesh `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182` without training or mutation.
- Locks separate ACTIVATED (100) and REPRESENTATIVE_HOLDOUT (160) registries with three-process deterministic rebuilds and zero overlap.

## Result

- Activated G0-G5: `{'G0': 20, 'G1': 20, 'G2': 20, 'G3': 20, 'G4': 10, 'G5': 10}`; quota `A1_ALL_TARGETS_MET`.
- One-step: 260 states / 1040 paired method records; represented false-safe=0.
- B3 rescued 20/20 G3 states over B2; the representative holdout selected 0 directional alternatives and added 0 segment/backup rejections.
- Bounded rollout: 640 episodes / 3603 logical steps.
- Offline reference collisions after commit: 0; no collision-superiority claim.
- B3 50 ms deadline miss rate: 44.62%; no real-time claim.

## Audits and boundaries

Fairness and selection-leakage audits pass. Activated data support mechanism existence only; representative prevalence remains separate. Represented-map certificates and offline-reference geometry are not conflated. No map training/mutation, data switch, parameter tuning, or protected-source mutation occurred. One same-manifest infrastructure resume was recorded before any completed formal output.

See `report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`, H1-H7 statistics, 32 figures, and the final validator result for full evidence.
