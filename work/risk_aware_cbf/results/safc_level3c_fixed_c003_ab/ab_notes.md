# SAFC Level-3C Fixed-C003 Targeted A/B Notes

## Scope

This is a fixed-C003 targeted A/B comparison between no-op execution and
warning-streak slowdown. It is not a full benchmark and does not claim
generalized performance improvement.

## Fixed Candidate

* C003
* flight trial 14
* selected from Level 3B-R and Level 3B-Active
* H3
* `dt_margin=0.0005`
* current official smoke wrapper
* `max_steps=100`

## Baseline No-Op

* Warning steps: 11
* First warning step: 60
* Collision: False
* QP infeasible: False
* Completed: False
* Stop reason: `stalled_before_goal`
* Command modified: False

## Active Slowdown

* Warning steps: 10
* First warning step: 60
* Slowdown-active steps: 10
* First slowdown step: 60
* Active scale range: [0.25, 0.75]
* Wrapper-level command scaled: True
* `u_nom` modified: False
* Internal `u_safe` modified: False

## A/B Observation

* Warning-step delta, active minus baseline:
  -1
* Baseline / active collision:
  False / False
* Baseline / active QP infeasible:
  False / False
* Baseline / active completed:
  False / False
* Release observed: False
* Fixed C003 observation: active recorded 1 fewer warning steps; baseline stop=stalled_before_goal, active stop=stalled_before_goal; baseline collision=False, active collision=False.

Because the active command can alter the subsequent trajectory,
post-activation comparisons are targeted behavioral observations rather than
same-trajectory causal proof.

## Claim Boundaries

* Targeted A/B only
* Single fixed candidate
* No full benchmark
* No statistical significance
* No generalized performance improvement
* No general collision reduction claim
* No general warning reduction claim
* No planner integration
* No real-robot validation
* No global safety guarantee
* No new CBF theorem
