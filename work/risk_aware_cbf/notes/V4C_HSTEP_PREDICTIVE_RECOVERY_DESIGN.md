# V4-C H-Step Predictive Safety Recovery Design

## Scope

This V4-C reproduction step only adds evaluation and recovery scripts under
`work/risk_aware_cbf/`. It does not modify the core SAFER-Splat implementation
in `cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, or `run.py`.

The goal is to test whether an H-step predictive recovery layer can reduce
short-horizon safety margin violations that survived V4-B one-step filtering.
The existing V4-B correction could not improve the immediate next-position
safety value because the current double-integrator Euler update makes the next
position depend on the current velocity rather than the just-selected
acceleration. V4-C therefore evaluates candidate control sequences over several
future integration steps, then executes only the first control.

## Baseline And Safety Query

The baseline control is still produced by the existing CBF path:

- `risk_aware_v1_bestD` maps to the existing V1 pre-CBF wrapper and risk score
  table.
- `safer_splat_filter` maps to the existing full SAFER-Splat CBF wrapper.

The safety value is the existing `GSplatLoader.query_distance(...,
distance_type="ball-to-ellipsoid")` value used by previous reproduction
scripts. It is not replaced by point cloud centers and is not treated as a
metric clearance in meters.

## H-Step Sequence Recovery

For each navigation step, the script rolls out the repeated baseline control
for `--horizon` steps and records:

- `base_horizon_min_h`: minimum safety value over the base H-step rollout.
- `base_next_h`: first-step safety value.
- `base_horizon_margin_violation`: whether `base_horizon_min_h < --dt-margin`.

Depending on `--activation-mode`, the script may generate candidate H-step
control sequences:

- `always`: run recovery at every step.
- `on_margin_violation`: run recovery only if the base H-step rollout violates
  `--dt-margin`.
- `on_warning`: run recovery if the base H-step rollout is below
  `--warning-margin`.

Candidate families:

- repeated baseline and scaled baseline controls;
- braking controls based on current velocity;
- repulsive controls from the current most critical ellipsoid;
- goal-directed controls;
- mixed sequences that reserve early steps for safety and later steps for the
  baseline or goal direction;
- random sequences around the baseline;
- optional CEM sequences when `--use-cem` is enabled.

Each candidate is rolled out for H steps with the repository's
`double_integrator_dynamics` function. A sequence is feasible if its horizon
minimum safety value is at least `--dt-margin`. Among feasible sequences, the
lowest weighted cost is selected. If no sequence is feasible, the sequence with
the largest horizon minimum safety value is selected and logged as a recovery
failure. Only the first control from the selected sequence is executed.

## Cost

The selection cost combines:

- control deviation from the CBF baseline;
- final goal distance after the H-step rollout;
- sequence smoothness;
- soft safety penalty for each horizon value below `--dt-margin`.

Weights are exposed by:

- `--w-base`
- `--w-goal`
- `--w-smooth`
- `--w-safety`

## Outputs

The runner writes:

- `trials.csv`
- `summary.csv`
- `metrics.json`
- `v4c_step_debug.csv`
- `v4c_sequence_debug.csv`
- `v4c_recovery_debug.csv`
- `comparison_plot.png`
- `run_log.txt`

The analysis script writes:

- `work/risk_aware_cbf/results/v4c_analysis_summary.csv`
- `work/risk_aware_cbf/figures/v4c_hstep_predictive_plots.png`
- `work/risk_aware_cbf/notes/V4C_ANALYSIS.md`
- `work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md`

## Success Criterion For Expanding To Flight20

The repair-needed run is eligible for a flight20 expansion only if:

- `collision_count == 0`
- `qp_infeasible_count == 0`
- `exec_horizon_margin_violation_count < base_horizon_margin_violation_count`

If this criterion is not met by the default configuration, the sweep script is
run on the repair-needed trials only. Flight20 is run only with a sweep
configuration satisfying the same criterion.
