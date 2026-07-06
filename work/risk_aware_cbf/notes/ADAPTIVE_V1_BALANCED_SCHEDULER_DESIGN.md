# Adaptive V1 Balanced Scheduler Design

## Motivation

The first Adaptive V1 scheduler established risk-responsive behavior: it increases the scheduled candidate budget on DT-warning and low-margin steps. However, the conservative profile is intentionally aggressive. In the hotspot offline replay, `selected_K_mean` is higher than fixed V1, `candidate_count_p95` reaches `8000`, and `recovery_support` / fallback is triggered often. This is useful as a conservative reference, but it is not yet an efficiency-improving adaptive budgeting policy.

The current evidence is still offline replay / audit. It proves scheduler behavior, not closed-loop runtime benefit. A balanced scheduler is needed to reduce overuse of max-budget fallback while preserving the response to DT Verification warnings and low-margin states.

## Design Goal

The balanced scheduler should:

- Preserve DT-warning and low-margin risk response.
- Reduce unnecessary `recovery_support` / fallback.
- Lower `selected_K_mean` and `selected_K_p95` relative to the conservative profile.
- Keep the interpretable `nominal`, `caution`, `critical`, and `recovery_support` structure.
- Keep Start-Safe CBF, DT Verification, and optional Predictive Recovery as the main safety framework.

Adaptive V1 remains a candidate budgeting / efficiency / risk-response support module. It is not a new CBF theorem and does not independently guarantee safety.

## Conservative Vs Balanced

The conservative profile uses max-budget fallback whenever the current safety value is at or below `dt_margin` and full-query fallback is enabled. This makes `current_h <= dt_margin` sufficient for `recovery_support`, even if no H-step DT warning is present.

The balanced profile makes fallback more selective:

- DT warning alone enters `critical`, not `recovery_support`.
- `current_h <= dt_margin` alone enters `critical`, not `recovery_support`.
- `current_h <= dt_margin` and DT warning together enter `recovery_support`.
- `recovery_active`, unresolved risk, candidate set empty / abnormal, or scheduler exception force `recovery_support` or safe fixed fallback.
- Full-query fallback is reserved for high-confidence critical cases or abnormal cases.

This design keeps high-risk budget escalation while avoiding max-budget overuse on single-signal states.

## Balanced Mode Rule

### Mode 0: nominal

Trigger:

- No DT warning.
- `current_h > h_caution_threshold`.
- Active constraints below caution threshold.
- Density below caution threshold.
- Speed below threshold.

Budget: `K_nominal = 1000`.

Expected behavior: reduce budget in easy regions.

### Mode 1: caution

Trigger:

- `current_h <= h_caution_threshold`, or
- high active constraints, or
- high density, or
- high speed,
- but no DT warning and no critical low-margin condition.

Budget: `K_caution = 2000`.

Expected behavior: keep fixed-level budget in mildly risky regions.

### Mode 2: critical

Trigger:

- DT warning is true, or
- `current_h <= h_critical_threshold`, or
- `current_h <= dt_margin` but no DT warning, or
- active constraints are very high, or
- density is very high.

Budget: `K_critical = 4000`.

Expected behavior: increase candidate coverage on sampled-data warning or low-margin states without always jumping to max budget.

### Mode 3: recovery_support / fallback

Trigger:

- `recovery_active` is true.
- `unresolved_risk` is true.
- Candidate set is empty or abnormal.
- Scheduler exception.
- `current_h <= dt_margin` and DT warning is true.
- Optional full-query fallback is explicitly requested in a high-confidence critical state.

Budget: `K_recovery = 8000`.

Expected behavior: reserve max-budget / full-query fallback for compound or abnormal risk, not every single low-margin signal.

## Reporting Requirements

Balanced scheduler results must be reported as offline replay / audit unless closed-loop navigation is explicitly run. `selected_K` is a scheduled budget proxy, not measured closed-loop candidate count. Runtime, collision, QP infeasibility, and H-step margin violations are inherited from the saved trajectory in offline replay.

The report must state:

- Balanced Adaptive V1 is not a standalone safety guarantee.
- Adaptive V1 does not replace Certified Feasibility-Aware Start-Safe CBF.
- Adaptive V1 does not replace DT Verification.
- Adaptive V1 does not replace optional Predictive Recovery.
- `min_safety_h` is the repository GSplat ellipsoid safety h value, not meter clearance.
- Margin violation is not collision.
- Offline replay is not closed-loop navigation.
- No official SAFER-Splat core source is modified.
- No new CBF theorem is claimed.
