# Lightweight MPC-style Recovery Targeted Pilot

## 1. Purpose

This report evaluates a first primitive-sequence MPC-style recovery pilot for FAS-CBF. It is a targeted offline pilot, not a full100 run and not an official benchmark result.

The goal is to test whether short recovery control sequences can improve H-step GSplat safety margin risk on DT-triggered states before any closed-loop integration.

## 2. Methodology Context

The intended framework remains:

1. Certified Feasibility-Aware Start-Safe CBF.
2. Discrete-Time Verification.
3. Optional triggered Predictive Recovery.

The MPC-style module is recovery second, triggered only after DT Verification warning / on-margin risk. It is not always-on, not a standalone safety guarantee, not a new CBF theorem, not a replacement for Start-Safe CBF, not a replacement for DT Verification, and not a replacement for CBF-QP safety filtering.

Margin violation is not collision. `min_safety_h` / `h` is the repository GSplat ellipsoid safety value, not metric clearance.

## 3. Relationship To Existing V4-C

Existing V4-C already provides triggered H-step predictive recovery. The new pilot makes the sequence structure explicit:

- generate length-H recovery control sequences,
- roll out every sequence under repository double-integrator dynamics,
- query GSplat safety h at each rollout step,
- choose a safety-feasible sequence or best-improving sequence,
- treat only the first control as the executed recovery action,
- re-enter DT Verification at the next step in a future closed-loop implementation.

This pilot does not replace the tested V4-C logic. It is an offline evaluator over saved trigger states.

## 4. Sequence Library

Implementation: `work/risk_aware_cbf/scripts/mpc_style_recovery_sequences.py`

Sequence families:

- `nominal_hold`
- deceleration / brake sequences
- lateral left / right sequences
- vertical up / down sequences
- brake + lateral sequences
- brake + vertical sequences
- goal-preserving bias sequences
- previous-safe-action smoothing sequences
- optional random shooting around the base action

Sanity check status: passed. The check covers shape, finite values, acceleration limit, deterministic random generation with seed, and nominal-sequence inclusion.

Default pilot controls:

- `accel_limit = 0.1`
- `lateral_scale = 0.05`
- `vertical_scale = 0.05`
- `brake_scale = 1.0`
- random shooting enabled by default for the N64 profiles

## 5. Targeted Pilot Setup

Input source:

`work/risk_aware_cbf/results/adaptive_v1_targeted_dt_risk_closed_loop/balanced/adaptive_v1_targeted_dt_risk_closed_loop_steps.csv`

Target trigger source:

`adaptive_v1_targeted_dt_risk_closed_loop` step CSV and target windows.

Targeted windows cover 199 trigger rows across trials 7, 9, 12, 13, and 14. This is a targeted DT-risk replay, not full100.

Profiles:

| profile | horizon | sequence count | dt margin | mode |
|---|---:|---:|---:|---|
| `primitive_h2_n64` | 2 | 64 | 0.0005 | offline evaluator |
| `primitive_h3_n64` | 3 | 64 | 0.0005 | offline evaluator |

Run robustness note:

The evaluator now writes progress every `--progress-every` triggers and partial outputs every `--save-every` triggers. It supports `--resume` and writes `mpc_style_recovery_trigger_rows.partial.csv` plus `mpc_style_recovery_metrics.partial.json`. The long H2/H3 targeted runs were executed as detached `nohup/setsid` jobs so IDE/Codex window reloads do not kill the experiment.

## 6. Results

Analyzer outputs:

- `work/risk_aware_cbf/results/mpc_style_recovery_targeted_pilot/analysis/mpc_style_recovery_summary.csv`
- `work/risk_aware_cbf/results/mpc_style_recovery_targeted_pilot/analysis/mpc_style_recovery_by_trial.csv`
- `work/risk_aware_cbf/results/mpc_style_recovery_targeted_pilot/analysis/mpc_style_recovery_by_sequence_type.csv`
- `work/risk_aware_cbf/results/mpc_style_recovery_targeted_pilot/analysis/mpc_style_recovery_metrics.json`

Summary:

| profile | triggers | success | improved but unresolved | no improvement | failed | base violations | selected violations | min base h | min selected h | h improvement mean | h improvement p95 | runtime mean | runtime p95 | runtime max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `primitive_h2_n64` | 199 | 103 | 0 | 96 | 0 | 101 | 96 | 0.000312344986 | 0.000312344986 | 1.39534e-07 | 4.71063e-07 | 2.3606 | 2.43675 | 2.64463 |
| `primitive_h3_n64` | 199 | 103 | 0 | 96 | 0 | 108 | 96 | 0.000298623345 | 0.000298623345 | 8.50932e-07 | 3.22027e-06 | 3.3939 | 3.48916 | 3.78611 |

No collision or QP-infeasible counts are reported by this evaluator because this is not closed-loop execution.

## 7. Sequence Type Analysis

Dominant selected sequence types:

| profile | dominant sequence types |
|---|---|
| `primitive_h2_n64` | `nominal_hold` 124, `smooth_previous_nominal` 60, `deceleration_0.5` 8, `previous_safe_hold` 3 |
| `primitive_h3_n64` | `nominal_hold` 121, `smooth_previous_nominal` 54, `deceleration_0.5` 8, `deceleration_0.25` 6, `previous_safe_hold` 4 |

Most no-improvement rows selected `nominal_hold`; this means the primitive sequence search often could not find a better safety-feasible action in the deepest low-margin segments. H3 increases the mean h improvement but does not reduce the selected margin violation count relative to H2.

By-trial failure concentration:

| profile | trial 12 selected violations | trial 13 selected violations | trial 14 selected violations |
|---|---:|---:|---:|
| `primitive_h2_n64` | 42 | 44 | 10 |
| `primitive_h3_n64` | 42 | 44 | 10 |

Trials 7 and 9 were fully successful for both H2 and H3; the unresolved cases are concentrated in trials 12, 13, and 14.

## 8. Comparison To Existing Recovery

Existing closed-loop references:

| reference | mode | base violations | exec violations | recovery success | runtime mean / p95 / max |
|---|---|---:|---:|---:|---|
| V4-C `H3_N128` full100 | closed-loop full100 | 236 | 0 | 236 | 0.170388 / 0.702523 / 1.638351 |
| V4-C `R4_H2_N64` full100 | closed-loop full100 | 193 | 0 | 193 | 0.095952 / 0.309428 / 0.654511 |

The MPC-style pilot is not directly comparable to these references:

- it is offline trigger-state replay,
- it does not execute a closed-loop trajectory,
- it uses targeted DT-risk windows, not official full100 starts,
- it does not produce collision or QP-infeasible outcomes.

Qualitative positioning:

- The primitive-sequence H2/H3 pilot does not show evidence that it is better than V4-C `R4_H2_N64`.
- It is slower than the closed-loop V4-C references in per-trigger evaluation time.
- It leaves 96 selected H-step margin violations in both H2 and H3 offline replay.
- The pilot is useful as a diagnostic of primitive sequence limitations, not as a replacement recovery method.

## 9. Decision

Continue MPC-style Recovery as the current candidate? No, not in this primitive N64 form.

Recommend closed-loop smoke? Not as the immediate next step for this exact profile. A closed-loop smoke is only worth doing after changing the sequence family, cost, or target selection because the current offline pilot leaves 96 selected margin violations.

Recommend flight20? No for this exact H2_N64/H3_N64 primitive profile.

Recommend full100 now? No.

Is it better than R4_H2_N64? No evidence. The comparison is not direct, and the observed offline metrics are weaker than the existing V4-C closed-loop evidence.

Paper positioning: optional recovery extension / future work. The result can be used to motivate that naive primitive-sequence MPC-style recovery is not enough and that the main contribution should remain Start-Safe CBF plus DT Verification, with V4-C recovery as an optional triggered module.

## 10. Limitations

- This is a targeted pilot, not full100.
- This is an offline evaluator, not closed-loop recovery.
- The target states come from saved Adaptive V1 targeted DT-risk results.
- MPC-style Recovery does not guarantee safety.
- No new CBF theorem is claimed.
- Margin violation is not collision.
- `h` / `min_safety_h` is not meter clearance.
- No official core source was modified.
- The tested MPC-style module is primitive-sequence / sampling-based, not full nonlinear MPC.
- V4-C remains an optional triggered recovery module and is not replaced by this pilot.
