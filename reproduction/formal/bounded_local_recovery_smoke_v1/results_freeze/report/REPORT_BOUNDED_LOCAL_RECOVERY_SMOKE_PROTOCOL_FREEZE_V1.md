# Bounded Local Recovery Smoke Protocol Freeze V1

## Status

PASS_FREEZE_BOUNDED_LOCAL_RECOVERY_SMOKE_PROTOCOL_V1

This is a protocol/harness freeze only. No Smoke trial, GPU rollout,
tmux execution session, or real PlantCommit was performed.

## Frozen authority

- implementation HEAD: 8184b0ecec20b6e84b1745518903b87bbb5cde8f
- Gate 0 HEAD: 18ba8ed8aa3b4acc326426e05808bd5abe67561c
- protocol commit: ae1aa239ac6b9950e5c1f89e57aff480dbadb7ee
- protocol SHA256: 16f3f81ee2b8b47f310130ae086a8211834727233d6c80b20df1cf4297d285ef
- semantic protocol SHA256: 320995a7ff1023aefd05a848d2cbdd4f984b22572d0d15ef425a58da6ce42bb9
- execution lock SHA256: f4e649f2f072a45e696b7c5629b4f6d6a5f571ed1296c1ff097fe0ffb436c7c0
- trial order SHA256: f65880d7fe3c1d8127b5cfbbeaff78c4fb462bb658e22d6ae0d69995afe4508a

## Cohort

- trials: [15, 45, 75]
- seed: 0
- max cycles per trial: 500
- serial: True
- separate process per trial: True

## Runtime authority

- physical GPU: 1
- CUDA_VISIBLE_DEVICES: 1
- child device: cuda:0
- result root: /disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_20260918
- tmux session: bounded_local_recovery_smoke_v1

## Recovery authority

- source: SOURCE_BOUNDED_LOCAL_RECOVERY_V1
- generator: AXIS_EXTREMA_F32_V1
- candidate family: F1_AXIS_EXTREMA_ONLY
- maximum candidates: 6
- order: ['+x', '-x', '+y', '-y', '+z', '-z']
- priority: ['CERTIFIED_PRIMARY', 'VALID_RETAINED_BACKUP', 'BOUNDED_LOCAL_RECOVERY', 'CERTIFIED_TERMINAL', 'ASSURANCE_BOUNDARY']

## Geometry

- hard radius: 0.015 q
- runtime margin: 0.0
- rho_seg: 0.0
- epsilon: None
- historical 0.025-q runtime authority: False

## Prelaunch CPU validation

- status: PASS_FREEZE_PRELAUNCH_CPU_VALIDATION_V1
- check count: 29
- GPU run count: 0
- tmux created count: 0
- Smoke trial run count: 0
- real PlantCommit count: 0

## Scientific boundary

Progress is diagnostic-only in this Smoke. No Reference pairing, no
bootstrap NI analysis, and no scientific efficacy claim are authorized.

The frozen scientific verdict remains:

FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE

## Next task

EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_V1
