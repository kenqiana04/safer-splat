# Bounded Local Recovery Engineering Pilot V1

This directory freezes a prospective, engineering-only pilot. It is not a scientific efficacy study, noninferiority test, Reference-arm experiment, safety proof, parameter-selection exercise, or paper-level result.

## Cohort

The requested anchors were `[12,15,24,45,68,75]`. Trials `15`, `45`, and `75` are Retry2 witnesses but are not members of the authoritative formal85 order, so they are recorded as missing and are not silently imported. The retained anchors are `[12,24,68]`. Nine controls are selected from the remaining formal85 order by the frozen evenly spaced index rule without consulting outcomes. The final order is:

`[66,12,88,24,2,14,63,36,58,68,62,77]`

The historical same-trial comparator is diagnostic only: `DIAGNOSTIC_HISTORICAL_SAME_TRIAL_NO_NI_NO_FORMAL_CAUSAL_CLAIM`.

## Future execution only

Run all commands from the worktree root:

```bash
cd /disk1/zlab/v3_repair_worktrees/safer-splat-freeze-bounded-local-recovery-engineering-pilot-v1
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_engineering_pilot_v1/validate_bounded_local_recovery_engineering_pilot_v1.py --mode prelaunch
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_engineering_pilot_v1/launch_bounded_local_recovery_engineering_pilot_v1.py \
  --launch --authorize-execution EXECUTE_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1
```

Future result root: `/disk1/zlab/v3_repair_records/bounded_local_recovery_engineering_pilot_v1_20260919`

Future tmux: `bounded_local_recovery_engineering_pilot_v1`

Execution is serial, one child process per trial, and has no automatic retry. If the result root already exists, do not relaunch.

## Monitor

The default output is a human-readable percentage display with overall and per-trial 30-character progress bars:

```bash
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_engineering_pilot_v1/monitor_bounded_local_recovery_engineering_pilot_v1.py
```

Use `--json` only for machine-readable output.

## Post-run analyzer

The analyzer is future-only and must also run from the worktree root so relative Stonehenge paths resolve to the frozen local bindings:

```bash
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_engineering_pilot_v1/analyze_bounded_local_recovery_engineering_pilot_v1.py \
  --authorize-postrun-analysis
```

It will produce hard-safety/integrity and recovery evidence plus `PILOT_PROGRESS_DIAGNOSTIC.json` and `PILOT_ROUTING_DIAGNOSTIC.json`. These are explicitly `NO_NI_NO_FORMAL_EFFICACY_CLAIM` diagnostics.

Retry2 remains `PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1`; the formal scientific verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`.
