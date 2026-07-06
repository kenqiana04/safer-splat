# Adaptive V1 Risk-Aware Candidate Budgeting Design

## Motivation

The current Risk-Aware V1 candidate budgeting is effective but mostly fixed: a fixed candidate budget, fixed thresholding rules, and fixed conservative level are used across low-risk and high-risk states. This is inefficient in easy parts of the trajectory and insufficiently expressive in high-risk parts where the controller is close to the discrete-time safety margin.

Adaptive V1 should make candidate coverage risk-responsive. Low-risk states can use a smaller budget because the current safety value is comfortably above the margin, DT Verification is quiet, velocity is low, and the local constraint set is not complex. High-risk states should use a larger budget because more Gaussian candidates may be needed to avoid missing near-active or future-active constraints.

DT Verification is a natural feedback signal for this module. It detects sampled-data H-step margin warnings that are not the same as collision and are not visible from collision counts alone. If DT Verification flags a warning, Adaptive V1 should increase candidate coverage. This does not replace DT Verification; it only uses the warning as an input to budget scheduling.

## Role In The Full Framework

The full FAS-CBF stack remains:

1. Certified Feasibility-Aware Start-Safe CBF.
2. Discrete-Time Verification.
3. Optional Predictive Recovery.

Adaptive V1 is an efficiency and risk-response support module inside this stack. It is not a new CBF theorem, not a standalone safety guarantee, not a replacement for full-query verification, not a replacement for DT Verification, and not a replacement for optional Predictive Recovery. It only schedules how much candidate coverage V1 should use before or around the existing CBF-QP machinery.

The official SAFER-Splat baseline source remains unchanged. Adaptive V1 is implemented as reproduction-side code under `work/risk_aware_cbf/`.

## Adaptive Signals

The scheduler supports the following signals. Every signal is optional so that missing fields can fall back to fixed V1 behavior.

- `current safety margin / min_safety_h`: low `min_safety_h` means the state is close to the repository GSplat ellipsoid safety boundary. This value is the repository safety h value, not meter clearance.
- `DT Verification warning flag`: an H-step sampled-data warning should increase candidate budget. The default practical trigger uses H=2, while H=3 remains a robust reference.
- `QP active or near-active constraints`: many active constraints indicate local geometric complexity or many constraints influencing the QP.
- `velocity norm / predicted displacement`: higher speed increases sampled-data risk because the next few steps can cover more space.
- `local Gaussian density or candidate count`: high local density increases the risk that too small a candidate set misses relevant Gaussians.
- `recovery mode flag`: when optional Predictive Recovery is triggered, V1 should support it with maximum budget or full-query fallback.

## Budget Scheduler

The initial scheduler is intentionally rule based and interpretable. It uses modes rather than a neural network or continuous learned policy.

The default budget levels are:

| mode | selected budget |
| --- | ---: |
| nominal | `K_nominal = 1000` |
| caution | `K_caution = 2000` |
| critical | `K_critical = 4000` |
| recovery-support / fallback | `K_recovery = 8000` |

All selected budgets are clipped into `[K_min, K_max]`.

### Mode 0: nominal

- Trigger condition: `min_safety_h` is comfortably above `h_caution_threshold`, no DT warning, moderate speed, moderate active constraint count, and moderate local density.
- Candidate budget: `K_nominal`.
- Threshold rule: no risk flag active.
- Fallback policy: if all required inputs are missing, fall back to fixed V1.
- Expected behavior: reduce unnecessary candidate coverage in easy regions.

### Mode 1: caution

- Trigger condition: `min_safety_h <= h_caution_threshold`, high speed, high active constraint count, or high local density.
- Candidate budget: `K_caution`.
- Threshold rule: any caution-level signal is active but no critical or fallback trigger is active.
- Fallback policy: if the caution signal is uncertain, keep the fixed V1 budget rather than dropping below it.
- Expected behavior: keep fixed-V1-level coverage when the state is not clearly low risk.

### Mode 2: critical

- Trigger condition: DT Verification warning, `min_safety_h <= h_critical_threshold`, or clearly high active constraint count.
- Candidate budget: `K_critical`.
- Threshold rule: any critical-level signal is active.
- Fallback policy: if the candidate set is missing or unreliable, escalate to recovery-support / fallback.
- Expected behavior: increase candidate coverage on sampled-data warning or near-margin steps.

### Mode 3: recovery-support / fallback

- Trigger condition: optional Predictive Recovery is triggered, unresolved margin risk remains, `min_safety_h <= dt_margin` with full-query fallback enabled, candidate set is empty, or the adaptive policy raises an exception.
- Candidate budget: `K_recovery` or max-budget / full-query fallback.
- Threshold rule: safety value is too low, recovery is active, or scheduler confidence is low.
- Fallback policy: use max budget or full-query verification fallback. If the scheduler itself fails, return original fixed V1 budget.
- Expected behavior: avoid under-budgeting when adaptive filtering may miss risk.

## Additive Interpretation

The scheduler can also be read as a clipped additive rule:

`K_t = clip(K_min + dK_margin + dK_DT + dK_active + dK_speed + dK_density, K_min, K_max)`

The implemented pilot reports mode decisions because they are easier to debug. The mode thresholds correspond to the same risk factors as the additive form.

## Fallback Design

The implementation must provide the following defensive paths:

- If `h_min` is too low, select recovery-support / fallback budget.
- If DT Verification reports a warning, increase budget at least to critical.
- If optional Predictive Recovery is triggered, use max budget or full-query verification fallback.
- If the candidate set is empty or abnormal, fall back to fixed V1 or recovery-support mode.
- If the adaptive policy receives missing inputs, return fixed V1 / nominal budget instead of under-budgeting.
- If the adaptive policy raises an exception, return the original fixed V1 budget.

## Metrics

The pilot must report:

- `runtime_mean`
- `runtime_p95`
- `runtime_max`
- `candidate_count_mean`
- `candidate_count_p95`
- `active_constraint_count_mean`
- `collision_count`
- `qp_infeasible_count`
- `min_safety_h_min`
- `H=1/H=2/H=3 margin violation count`
- `DT warning count`
- `fallback_count`
- `mode counts`

For offline replay, `candidate_count` means scheduled candidate budget, not measured closed-loop candidate count. Runtime, collision, QP infeasibility, and safety values are inherited from the saved trajectory and must not be described as new closed-loop navigation results.

## Pilot Plan

The first implementation should not default to full100. The sequence is:

1. Scheduler sanity check with fake signals.
2. Smoke offline replay on trial 0, first 5 steps, fixed and adaptive.
3. Hotspot offline replay on trials `85,37,13,31,12,14`.
4. Analyze whether adaptive mode increases budget on DT-warning and low-margin steps.
5. Decide whether to run flight20 or a closed-loop pilot.

Only after smoke and hotspot behavior are stable should a flight20 or full100 experiment be considered.

## Reporting Constraints

The report must state:

- Adaptive V1 does not modify official SAFER-Splat core source.
- Adaptive V1 does not claim a new CBF theorem.
- Adaptive V1 does not independently guarantee safety.
- Adaptive V1 does not replace DT Verification.
- Adaptive V1 does not replace optional Predictive Recovery.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- Offline replay is not closed-loop navigation.
