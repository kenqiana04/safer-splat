# SAFC Level-3E Robustness and Failure-Diagnosis Notes

## Scope

This is a bounded robustness and failure-diagnosis audit over the Level-3D
small targeted cohort. It is not a full benchmark and does not claim
generalized performance improvement.

## Why Level 3E Was Needed

Level 3D overall warning steps decreased, but C004 became worse, C006 was
neutral, and no run completed. Therefore robustness and failure diagnosis is
needed before any final method-validation package.

## Preregistered Variants

* current_policy: warning=0.75, persistent=0.5, critical=0.25, min=0.25
* milder_slowdown: warning=0.85, persistent=0.7, critical=0.5, min=0.5
* critical_only_slowdown: warning=1.0, persistent=1.0, critical=0.5, min=0.5

These variants diagnose whether slowdown scale aggressiveness changes warning
count, stop reason, or compact progress behavior.

## Mixed Outcome Diagnosis

* C004: milder_policy_helpful; current=68, milder=64, critical-only=64. Negative evidence is retained.
* C006: slowdown_neutral; current=41, milder=41, critical-only=41.
* Positive candidates C003/C002/C001 are reported in compact tables; variant differences remain diagnostic only.

Per-run compact summaries:

* C003 / current_policy: warnings=10, stop=`stalled_before_goal`, progress_proxy=0.051808953285217285
* C003 / milder_slowdown: warnings=11, stop=`stalled_before_goal`, progress_proxy=0.052411824464797974
* C003 / critical_only_slowdown: warnings=11, stop=`stalled_before_goal`, progress_proxy=0.052411824464797974
* C004 / current_policy: warnings=68, stop=`max_steps`, progress_proxy=0.15519338846206665
* C004 / milder_slowdown: warnings=64, stop=`max_steps`, progress_proxy=0.15848422050476074
* C004 / critical_only_slowdown: warnings=64, stop=`max_steps`, progress_proxy=0.15848422050476074
* C002 / current_policy: warnings=24, stop=`max_steps`, progress_proxy=0.1938244104385376
* C002 / milder_slowdown: warnings=34, stop=`max_steps`, progress_proxy=0.19403699040412903
* C002 / critical_only_slowdown: warnings=34, stop=`max_steps`, progress_proxy=0.19403699040412903
* C001 / current_policy: warnings=21, stop=`max_steps`, progress_proxy=0.1819528341293335
* C001 / milder_slowdown: warnings=32, stop=`max_steps`, progress_proxy=0.1822555661201477
* C001 / critical_only_slowdown: warnings=32, stop=`max_steps`, progress_proxy=0.1822555661201477
* C006 / current_policy: warnings=41, stop=`max_steps`, progress_proxy=0.217196524143219
* C006 / milder_slowdown: warnings=41, stop=`max_steps`, progress_proxy=0.21617314219474792
* C006 / critical_only_slowdown: warnings=41, stop=`max_steps`, progress_proxy=0.21617314219474792

## Stop Reason Diagnosis

Completed counts are current=0,
milder=0, critical-only=0.
The compact progress proxy is available as goal-distance reduction, but it is
not a proof of task completion or planner quality. Stop-reason effects remain
diagnostic observations.

## Claim Boundaries

* diagnostic audit only
* no full benchmark
* no statistical significance
* no generalized performance improvement
* no generalized collision reduction
* no generalized warning reduction
* no planner integration
* no real-robot validation
* no global safety guarantee
* no new CBF theorem
