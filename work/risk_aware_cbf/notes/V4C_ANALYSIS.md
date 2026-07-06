# V4-C H-Step Predictive Safety Recovery Report

## Scope

This task only evaluates the V4-C H-step predictive recovery layer under
`work/risk_aware_cbf/` for the dense `flight` scene. It is not a full
SAFER-Splat paper reproduction.

No core algorithm source was modified. The forbidden source areas
`cbf/`, `splat/`, `ellipsoids/`, `dynamics/`, and `run.py` were checked with
`git diff --name-only -- cbf splat ellipsoids dynamics run.py`, and no modified
files were reported.

The safety value is the repository's existing GSplat ellipsoid safety query:
`GSplatLoader.query_distance(..., distance_type="ball-to-ellipsoid")`. It is
not a point-cloud-center approximation and should be read as the repository
safety `h` value, not a metric clearance in meters.

## Implemented Files

- `work/risk_aware_cbf/notes/V4C_HSTEP_PREDICTIVE_RECOVERY_DESIGN.md`
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py`
- `work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_sweep.py`
- `work/risk_aware_cbf/scripts/analyze_v4c_results.py`
- `work/risk_aware_cbf/results/v4c_analysis_summary.csv`
- `work/risk_aware_cbf/figures/v4c_hstep_predictive_plots.png`
- `work/risk_aware_cbf/notes/V4C_ANALYSIS.md`
- `work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md`

## Method

V4-C keeps the existing CBF baseline control from `risk_aware_v1_bestD`.
At each step it rolls out the repeated baseline control over a short horizon
and checks the minimum safety value across that horizon.

Default configuration:

- scene: `flight`
- method: `risk_aware_v1_bestD`
- horizon: `3`
- num sequences: `128`
- activation mode: `on_margin_violation`
- dt margin: `0.0005`
- warning margin: `0.0008`
- control scales: `0,0.25,0.5,0.75,1.0`
- candidate families: braking, repulsive, goal-directed, mixed, random around
  base, and repeated baseline sequences

If a baseline H-step rollout violates the margin, V4-C selects a candidate
sequence by lowest weighted cost among feasible sequences. If no feasible
sequence exists, it selects the sequence with the largest horizon minimum
safety value and marks recovery as failed. Only the first control of the
selected sequence is executed.

## Results

| run | rows | collision_count | qp_infeasible_count | base_horizon_margin_violation_count | exec_horizon_margin_violation_count | reduction | recovery_used | recovery_success | recovery_failed | min_safety_h_min | runtime_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| repair-needed 8 | 8 | 0 | 0 | 9 | 0 | 9 | 9 | 9 | 0 | 0.0005000751698389649 | 0.10484686020206391 |
| flight20 | 20 | 0 | 0 | 60 | 0 | 60 | 60 | 60 | 0 | 0.0005005347775295377 | 0.24179199308067217 |

The default repair-needed run met the expansion criterion:

- `collision_count == 0`
- `qp_infeasible_count == 0`
- `exec_horizon_margin_violation_count < base_horizon_margin_violation_count`

Therefore the sweep was not run. The same default configuration was expanded
to `flight20`.

## Interpretation

V4-C addresses the V4-B failure mode. V4-B's one-step corrective control could
not change the immediate next position under the current Euler double-integrator
update, so it did not reduce position-based safety margin violations. V4-C
checks multiple future steps before choosing the first control. On the
repair-needed subset, it reduced H-step margin violations from 9 to 0. On
flight20, it reduced H-step margin violations from 60 to 0.

The cost is runtime. Most non-activated trials run near the original V1 timing,
but activated trials with many sequence evaluations are much slower. In
flight20, trials 12, 13, and 14 account for most of the runtime increase because
they trigger H-step recovery repeatedly.

## Key Output Paths

- repair-needed trials: `work/risk_aware_cbf/results/v4c_hstep3_flight_repair_needed_v1_bestD/trials.csv`
- repair-needed summary: `work/risk_aware_cbf/results/v4c_hstep3_flight_repair_needed_v1_bestD/summary.csv`
- flight20 trials: `work/risk_aware_cbf/results/v4c_hstep3_flight20_v1_bestD/trials.csv`
- flight20 summary: `work/risk_aware_cbf/results/v4c_hstep3_flight20_v1_bestD/summary.csv`
- combined analysis: `work/risk_aware_cbf/results/v4c_analysis_summary.csv`
- plot: `work/risk_aware_cbf/figures/v4c_hstep_predictive_plots.png`

## Remaining Limitations

This is still a reproduction-side evaluation layer, not a production navigation
algorithm change. It only covers dense `flight` with `risk_aware_v1_bestD`, the
repair-needed 8 trials, and the first 20 official flight trials. It does not
replace the core SAFER-Splat implementation and does not establish full paper
reproduction.
