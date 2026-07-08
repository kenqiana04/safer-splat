# Lightweight MPC-Style Recovery Design

## 1. Purpose

This design extends the existing triggered V4-C recovery idea from single-action H-step predictive rollout toward a lightweight MPC-style recovery. The implementation is primitive-sequence / sampling-based receding-horizon recovery, not full nonlinear constrained MPC.

The objective is to test whether short recovery control sequences can improve H-step safety margins on targeted DT-risk states before considering any closed-loop or larger benchmark.

## 2. Relationship To Current Framework

The method hierarchy remains:

1. Certified Feasibility-Aware Start-Safe CBF.
2. Discrete-Time Verification.
3. Optional triggered recovery.

MPC-style Recovery is recovery second, after DT Verification detects warning / on-margin risk. It is not always-on, not an independent safety guarantee, not a new CBF theorem, not a replacement for Start-Safe CBF, and not a replacement for DT Verification or CBF-QP safety filtering.

## 3. Current V4-C Limitation

Current V4-C already performs H-step predictive evaluation and executes only the first control of the selected candidate. However, the current tested configurations are closer to evaluating sampled recovery actions or repeated short-horizon controls than explicitly optimizing a structured future control sequence.

A lightweight sequence-based version can make the receding-horizon structure explicit:

- generate multiple length-H primitive sequences,
- roll out each sequence,
- evaluate safety and smoothness costs,
- execute only the first control,
- re-check DT Verification at the next step.

## 4. Proposed Lightweight MPC-Style Recovery

For each triggered state, generate candidate sequences:

`U = [u_t, u_{t+1}, ..., u_{t+H-1}]`

Each sequence is rolled out with the repository double-integrator dynamics. GSplat safety h values are queried at every rollout step. The evaluator selects either the lowest-cost safety-feasible sequence or the best-improving sequence when no candidate reaches the DT margin.

Only `u_t` is treated as the executed recovery action. The next control step must repeat DT Verification before any further recovery action.

## 5. Primitive Sequence Families

The first sequence library includes:

- nominal hold,
- deceleration / braking sequences,
- lateral left / right sequences,
- vertical up / down sequences,
- brake + lateral sequences,
- brake + vertical sequences,
- goal-preserving safety-bias sequences,
- previous-safe-action smoothing sequences,
- optional random shooting around the nominal/base action.

## 6. Cost Design

The safety-aware sequence cost is:

`J(U) = w_goal * goal_error + w_safe * safety_penalty + w_control * control_effort + w_smooth * action_smoothness + w_deviation * nominal_deviation + w_terminal * terminal_safety_penalty`

Safety penalty:

- max violation penalty: `max_k max(0, dt_margin - h(x_{t+k}))^2`
- sum violation penalty: `sum_k max(0, dt_margin - h(x_{t+k}))^2`
- terminal penalty: `max(0, dt_margin - h(x_{t+H}))^2`
- optional reward/rank from `min_k h(x_{t+k})`

## 7. Success Taxonomy

- `success`: selected sequence H-step rollout has no margin violation.
- `improved_but_unresolved`: selected sequence improves min H-step h but remains below `dt_margin`.
- `no_improvement`: selected sequence does not improve min H-step h.
- `failed`: no valid candidate sequence, rollout error, or all candidates invalid.

Margin violation is not collision. `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.

## 8. Metrics

The targeted pilot reports:

- trigger_count,
- recovery_attempt_count,
- recovery_success_count,
- improved_but_unresolved_count,
- no_improvement_count,
- recovery_failed_count,
- base_horizon_margin_violation_count,
- exec_horizon_margin_violation_count,
- min_base_horizon_h,
- min_exec_horizon_h,
- h_improvement_mean / p95,
- runtime_mean / p95 / max,
- selected_sequence_type counts,
- control_smoothness,
- nominal_deviation,
- progress proxy,
- collision_count and QP infeasible count when available.

For the offline evaluator, collision and QP counts are inherited only if present in input logs; otherwise they are not closed-loop results.

## 9. Comparison Target

The relevant comparison targets are:

- existing R4_H2_N64 as the dense-flight practical tested V4-C configuration,
- optional H3_N128 as robust reference,
- new primitive-sequence MPC-style recovery as targeted offline evaluator.

Direct comparison requires the same closed-loop states and execution mode. If exact R4 states are not available, the report must state that the comparison is not directly comparable.

## 10. Stage Decision

- If the targeted pilot cannot improve over the R4_H2_N64 reference signal, do not continue to full100.
- If runtime is excessive, downgrade to future work.
- If margin improvement or smoothness is useful and runtime is controlled, the next step can be a closed-loop smoke.
- This phase does not run full100.

