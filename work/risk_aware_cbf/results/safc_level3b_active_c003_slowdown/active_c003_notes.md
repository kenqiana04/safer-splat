# SAFC Fixed-Candidate Level-3B-Active C003 Notes

## Scope

This is a fixed-candidate targeted activation smoke. It tests warning-gated
slowdown activation on C003 only. It is not a benchmark and does not claim
performance improvement.

## Candidate Context

* C003
* flight trial 14
* selected because Level 3B-R reproduced H3 warning at step 60
* H3
* `dt_margin=0.0005`
* current official smoke wrapper
* `max_steps=100`

## No-Op Precheck

* Natural warning reproduced: True
* Natural warning steps: 11
* First warning step: 60
* Command modified: False

## Active Slowdown Smoke

* Active-run natural warning steps: 10
* First active-run warning step: 60
* Slowdown-active steps: 10
* First slowdown step: 60
* Active scale range: [0.25, 0.75]
* Wrapper-level command scaled: True
* Release observed: False
* `u_nom` modified: False
* Internal `u_safe` modified: False

## Claim Boundaries

* Targeted activation only
* No full benchmark
* No performance improvement
* No collision reduction
* No warning reduction
* No planner integration
* No real-robot validation
* No global safety guarantee
* No new CBF theorem
