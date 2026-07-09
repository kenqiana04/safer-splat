# REPORT: SAFC Level-3A Warning-Streak Slowdown

## 1. Purpose

This report evaluates whether the minimal active SAFC feedback policy,
warning-streak slowdown, has correct bounded policy logic and can be integrated
into an existing tiny closed-loop smoke path.

This is not a full benchmark. It does not claim that SAFC improves safety
performance, reduces collisions, reduces warnings, or improves planning
accuracy.

## 2. Setup

- Branch: `safc-level3a-warning-slowdown`
- Base commit: `4d157fb8b8844daf9eae773ad9a4221212b46b96`
- Selected entrypoint:
  `reproduction/scripts/run_official_runpy_smoke.py`
- Mode: `policy-harness-and-smoke`
- Scene and trial: `stonehenge_trial0`
- `max_trials`: 1
- `max_steps`: 20
- Policy scales: warning 0.75, persistent 0.50, critical 0.25
- Minimum scale: 0.25
- Maximum scale change per step: 0.25
- Official core source modified: false
- Controller modified: false
- CBF-QP modified: false
- Dynamics modified: false

The remote smoke used the existing `safer_splat_official` environment on GPU
1. Temporary files and the Matplotlib configuration were directed to
`/disk1/zlab/tmp`; the existing wrapper was imported without invoking its
trajectory-writing `main` function.

## 3. Method

### 3.1 Policy Logic Harness

Ten synthetic event snapshots tested no-warning behavior, first and persistent
H1 warnings, H2 and H3 warnings, a critical warning streak, release hysteresis,
QP infeasibility handoff, and collision handoff. These snapshots test policy
logic only and are not closed-loop performance evidence.

All ten cases had to pass before the smoke was allowed to run. Each decision
was checked for its expected activity state, scale range, boundedness,
control-modification flag, and claim scope.

### 3.2 Closed-Loop Active Smoke

One 20-step smoke was run through an external Level-3A wrapper around the
existing official smoke entrypoint. A natural GSplat distance warning was
required before the wrapper could scale a command. The policy did not inject
warnings.

The original `u_nom` and internal CBF-QP `u_safe` remained unchanged. If the
warning gate had opened, scaling would have applied only to the wrapper-level
executed command. No planner, replanning, risk-cost integration, waypoint
screening, CBF-QP change, or dynamics change was involved.

## 4. Results

| Metric | Value |
| --- | ---: |
| `policy_harness_cases` | 10 |
| `policy_harness_passed` | true |
| `trials_observed` | 1 |
| `steps_observed` | 20 |
| `natural_warning_steps` | 0 |
| `slowdown_active_steps` | 0 |
| `min_scale_applied` | 1.0 |
| `max_control_delta_from_slowdown` | 0.0 |
| `command_modified_only_when_warning` | true |
| `u_nom_modified` | false |
| `u_safe_internal_modified` | false |
| `wrapper_exec_command_scaled` | false |
| `collision_observed` | false |
| `qp_infeasible_observed` | false |
| `recovery_used_observed` | false |
| `activation_observed` | false |

The policy harness passed. The closed-loop smoke completed without a natural
warning, so the warning gate never opened and the executed command was not
scaled.

## 5. Interpretation

No natural warning was observed in the tiny smoke, so the active slowdown
policy was not exercised in closed-loop. The result validates policy logic and
safe integration but not active-policy effectiveness.

The zero control delta is the expected no-activation result. It is not evidence
that slowdown improves a safety or performance metric.

## 6. What Level 3A Validates

- Bounded warning-streak slowdown policy logic.
- An active feedback code path exists at the wrapper level.
- Integration does not modify CBF-QP or dynamics.
- Command scaling is gated by natural warning conditions.
- Compact summaries are generated without raw traces.

## 7. What Level 3A Does Not Validate

- No full benchmark.
- No safety performance improvement.
- No collision reduction.
- No warning reduction.
- No planner integration.
- No real-robot validation.
- No global safety guarantee.
- No new CBF theorem.

## 8. Decision

Do not proceed directly to performance claims. A separate Level 3B experiment
must first identify a legitimate naturally warning-rich targeted scenario.
Artificial warning injection may remain in a policy logic harness, but it
cannot be presented as natural closed-loop evidence.

SAFC Level 3A validates bounded warning-streak slowdown policy logic and
tiny-smoke integration only.

The active policy was not exercised by natural warnings in the tiny smoke;
therefore Level 3A validates policy logic and integration, not active-policy
effectiveness.
