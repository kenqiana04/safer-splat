# REPORT: SAFC Level-2 No-Op Closed-Loop Instrumentation

## 1. Purpose

This report evaluates whether SAFC can be inserted as a passive supervisory
logger in an existing closed-loop smoke path without changing nominal,
filtered, or executed controls. It records online state decisions and feedback
candidates, then writes only compact aggregate summaries.

This is not an active feedback experiment. It does not test slowdown,
replanning, risk-cost update, or waypoint screening. It does not claim
safety-performance improvement.

## 2. Setup

| Item | Value |
| --- | --- |
| branch | `safc-level2-noop-instrumentation` |
| base commit | `8920027886c6f3b04e6cb0cd8c43ffaee8d83ccb` |
| execution host | 4090 server |
| selected entrypoint | `reproduction/scripts/run_official_runpy_smoke.py` |
| scene | `stonehenge` |
| max trials | 1 |
| max steps | 20 |
| mode | `noop` |
| equivalence mode | `strong_action_delta_check` |
| official core source modified | false |
| controller modified | false |

The existing one-trial smoke wrapper was imported from the execution host as a
module. Its scene definition, loader, CBF class, and dynamics interface were
reused, but its `main` function was not called because that path writes a
trajectory CSV and plot. The Level-2 runner was executed from `/disk1/zlab/tmp`
and did not write into the remote Git working tree.

## 3. Method

The runner performs the following bounded procedure:

1. audit available execution entrypoints and select the existing short smoke
   wrapper;
2. load the existing official `stonehenge` checkpoint;
3. run one baseline trial for at most 20 closed-loop steps;
4. build scalar/Boolean SAFC event snapshots at each step;
5. call the no-op state-machine helper to obtain only a state decision and
   feedback candidate;
6. reread `u_nom`, `u_safe`, and `u_exec` from the unchanged original
   variables after each decision;
7. execute the original baseline `u` variable; and
8. aggregate transitions, candidates, equivalence values, and event counts
   without writing a per-step trace.

The helper neither accepts nor returns an action vector. Every decision carries
`no_op=true` and `modifies_control=false`.

## 4. No-Op Equivalence

| Metric | Value |
| --- | --- |
| `equivalence_check_strength` | `strong_action_delta_check` |
| `max_abs_delta_u_nom` | 0.0 |
| `max_abs_delta_u_safe` | 0.0 |
| `max_abs_delta_u_exec` | 0.0 |
| `all_decisions_no_op` | true |
| `any_modifies_control` | false |
| `noop_equivalence_passed` | true |

This is a strong action-delta check rather than only a structural check. The
runner measures command values immediately before and after the passive SAFC
decision on every observed step. The original baseline command variable is
then used for execution. All three maximum deltas are exactly zero.

## 5. Instrumentation Results

| Metric | Value |
| --- | ---: |
| `trials_observed` | 1 |
| `steps_observed` | 20 |
| `safc_decisions_logged` | 20 |
| `state_transition_groups` | 3 |
| `feedback_candidate_groups` | 2 |
| `dt_warning_steps_observed` | 0 |
| `recovery_candidate_steps_observed` | 0 |
| `safe_halt_candidate_steps_observed` | 0 |
| `replan_request_candidate_steps_observed` | 0 |
| `collision_steps_observed` | 0 |
| `qp_infeasible_steps_observed` | 0 |

The observed transition groups were S0 -> S1 for start admission, S1 -> S2 for
successful nominal filtering without a warning, and S2 -> S2 for continued
verified execution. The two logged feedback candidate groups were
`admit_task` and `no_feedback`. These observations describe only this tiny
smoke and are not evidence that SAFC reduces warnings or collisions.

## 6. What Level 2 Validates

Level 2 validates only that:

- SAFC can be inserted as a no-op supervisory logger in the selected tiny
  closed-loop smoke path;
- SAFC can produce online state and feedback-candidate records;
- no-op instrumentation does not modify control under the checked strong
  action-delta equivalence mode; and
- compact summaries can be generated without raw traces or per-step dumps.

SAFC Level 2 validates no-op closed-loop instrumentation feasibility and
control non-interference in a tiny smoke scope.

## 7. What Level 2 Does Not Validate

Level 2 provides:

- no active feedback validation;
- no performance-improvement evidence;
- no collision-reduction evidence;
- no warning-reduction evidence;
- no planner-improvement or planner-integration evidence;
- no real-robot deployment evidence;
- no global safety guarantee; and
- no new CBF theorem.

The zero warning, collision, and infeasibility counts are observations from one
20-step smoke, not improvements attributable to SAFC.

## 8. Decision

Level 2 is sufficient to proceed to a carefully bounded Level 3 minimal active
feedback policy, such as warning-streak slowdown, but only in a new branch and
with smoke-first validation. Level 2 itself remains passive instrumentation.
