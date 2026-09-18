# Bounded Local Recovery Smoke V1

Development-only GPU engineering smoke for the frozen
CERTIFIED_BOUNDED_LOCAL_RECOVERY V1 implementation.

This protocol freeze does not establish scientific efficacy and does not
revise FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE.

Frozen cohort:
- trials: [15, 45, 75]
- seed: 0
- maximum cycles per trial: 500
- serial execution
- separate process per trial

Frozen device mapping:
- physical GPU: 1
- CUDA_VISIBLE_DEVICES: 1
- child runtime device: cuda:0

Frozen recovery:
- source: SOURCE_BOUNDED_LOCAL_RECOVERY_V1
- generator: AXIS_EXTREMA_F32_V1
- family: F1_AXIS_EXTREMA_ONLY
- maximum candidates: 6
- order: +x, -x, +y, -y, +z, -z

Safe CLI inspection:
  python run_bounded_local_recovery_smoke_trial_v1.py --help
  python launch_bounded_local_recovery_smoke_v1.py --help
  python validate_bounded_local_recovery_smoke_v1.py --help
  python monitor_bounded_local_recovery_smoke_v1.py --help
  python analyze_bounded_local_recovery_smoke_v1.py --help

Freeze validation:
  python validate_bounded_local_recovery_smoke_v1.py --mode freeze

Future prelaunch validation after execution lock creation:
  python validate_bounded_local_recovery_smoke_v1.py --mode prelaunch

Future execution requires the explicit launcher authorization token:
  EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_V1

No Reference pairing, bootstrap non-inferiority analysis, or scientific
progress claim belongs to this engineering smoke.

## R1 local-infrastructure binding repair

Attempt0 root is immutable:

`/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_20260918`

Attempt0 stopped before the first completed control cycle because the new Git
worktree did not contain the ignored local `outputs/stonehenge` binding required
by the legacy V3 stack. It produced zero completed cycles and zero PlantCommit,
so it is execution-harness evidence, not bounded-recovery method evidence.

Retry1 root:

`/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_retry1_20260918`

Required local ignored bindings:

- `outputs/stonehenge` -> `/disk1/zlab/projects/safer-splat/outputs/stonehenge`
- `data/stonehenge` -> `/disk1/zlab/projects/safer-splat/data/stonehenge`

The prelaunch validator checks both bindings before any GPU launch. These
bindings have no routing, controller, CBF, geometry, candidate, or scientific
authority.
