# FC-Aware V1 Capped Closed-Loop Smoke Design

## Purpose

This task runs a wrapper-level capped closed-loop smoke for FC-Aware V1. It tests only `nearest_first + heading cap 16000` and is not a full100 benchmark, not final method validation, and not a safety guarantee.

## Why nearest_first cap16000

The exact recall audit found that `nearest_first` is deployable and that cap16000 retained exact dual-active, tight, low-h, and combined-risk recall with minimum recall 1.0 over the targeted risk-window rows. It also had zero dropped dual-active, tight, and low-h candidates, with mean reduction ratio 0.342879. Oracle rankings remain diagnostic only and are not used for closed-loop smoke.

## Wrapper-Level Implementation

The official candidate selector and core source are not modified. A wrapper selector in `work/risk_aware_cbf/` reconstructs V1 source groups, keeps near candidates, keeps history candidates conservatively, ranks heading candidates by nearest distance, retains the top 16000 heading IDs, and then applies the same optional risk-ranked fill rule when needed. If required fields are missing or the cap cannot be applied safely, the wrapper falls back to full heading candidates and records `fallback_reason`.

## Smoke Scope

The staged scope is:

1. trial 12, max_steps 20.
2. trial 13, max_steps 20 if trial 12 passes.
3. trial 12, max_steps 80 if both step20 smokes pass.

No flight20, no full100, and no V4-C recovery are run.

## Metrics

The smoke records runtime mean/p95/max, measured candidate count mean/p95/max, heading count before/after, final candidate count before/after, cap applied count, fallback count and reasons, collision count, QP infeasible count, min_safety_h minimum, H1/H2/H3 margin violation counts, DT warning count, low-margin count, selected_K, heading cap, progress mean, and recovery_used_count.

## Pass / Fail Criteria

Pass requires:

- no crash,
- cap applied for capped profile,
- collision_count = 0,
- qp_infeasible_count = 0,
- min_safety_h not worse than fixed beyond tolerance,
- H1/H2/H3 margin violations not increased,
- measured final candidate count reduced,
- fallback path available,
- recovery_used_count = 0.

Stop or do not expand if collision appears, QP infeasible appears, min_safety_h worsens, DT/H-step margin violations increase, the wrapper cannot apply the cap, candidate fields are missing, or fallback is broken.
