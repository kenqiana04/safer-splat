# Bounded Local Recovery Smoke R1 Local-Infra Repair Freeze

## Status

PASS_FREEZE_BOUNDED_LOCAL_RECOVERY_SMOKE_LOCAL_INFRA_BINDING_R1

## Attempt0

- root: `/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_20260918`
- classification: `EXECUTION_HARNESS_LOCAL_INFRA_BINDING`
- trial: `15`
- process exit code: `2`
- completed cycles: `0`
- PlantCommit: `0`
- recovery attempts: `0`
- method evidence: `NONE`
- mutation authorized: `false`

## Repair

- outputs binding source: `/disk1/zlab/projects/safer-splat/outputs/stonehenge`
- data binding source: `/disk1/zlab/projects/safer-splat/data/stonehenge`
- runtime/method diff: `0`
- hard geometry change: `0`
- recovery candidate change: `0`
- scientific verdict change: `0`

## Retry1

- result root: `/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_retry1_20260918`
- protocol commit: `fd32fae67f8292f20196478eba7a43039e720e64`
- protocol SHA256: `c369f8b2a0376b0b6fb0a7778d15ce694aa394780d4f50acb462d11ae798bf57`
- semantic protocol SHA256: `177212f75ac3706af8d58cad14ae55345da5c1e4967092a0c326ad5f1345777b`
- execution lock SHA256: `e838c309cff52f98088156017e2dc00340d81793aa7e019d3561348cad149d61`
- trial order: `[15, 45, 75]`

## Prelaunch

- status: `PASS_FREEZE_PRELAUNCH_CPU_VALIDATION_V1`
- check count: `31`
- local outputs binding: `PASS`
- local data binding: `PASS`
- GPU run count: `0`
- tmux created count: `0`
- Smoke trial run count: `0`
- real PlantCommit count: `0`

## Scientific boundary

The bounded-recovery method has not been re-evaluated by this repair freeze.
The frozen scientific verdict remains:

`FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`

## Only next task

`EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY1_V1`
