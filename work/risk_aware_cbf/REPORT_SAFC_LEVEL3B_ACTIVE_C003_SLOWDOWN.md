# REPORT: SAFC Fixed-Candidate Level-3B-Active C003 Slowdown

## 1. Purpose

This report tests whether warning-streak slowdown activates after a naturally
observed warning on the fixed C003 candidate reproduced by Level 3B-R.

This is not a full benchmark. It does not claim that SAFC improves safety
performance, reduces collisions, reduces warnings, or improves planning
accuracy.

## 2. Setup

| Item | Value |
| --- | --- |
| Branch | `safc-level3b-active-c003-slowdown` |
| Base commit | `62ee6b9c34afa393f03c2dc9d7ccaa5f22ad108d` |
| Candidate | C003 |
| Scene / trial | flight / 14 |
| Entrypoint | `reproduction/scripts/run_official_runpy_smoke.py` |
| DT margin | 0.0005 |
| Horizon | H3 |
| Maximum steps | 100 |
| Policy | warning-streak slowdown |
| Warning / persistent / critical scale | 0.75 / 0.50 / 0.25 |
| Minimum scale | 0.25 |
| Official core source modified | false |
| Controller modified | false |
| CBF-QP modified | false |
| Dynamics modified | false |

The run used the existing `safer_splat_official` environment on GPU 1. Temporary
execution files were placed under `/disk1/zlab/tmp`; no raw trace or per-step
artifact was retained.

## 3. Method

### 3.1 No-op precheck

Stage A reran fixed C003 with repeated-control H1/H2/H3 verification and
`dt_margin=0.0005`. It executed the original `u_safe` unchanged. No slowdown,
recovery, or planner action was enabled. Stage B was permitted only after at
least one natural warning was observed.

### 3.2 Active slowdown smoke

Stage B restarted the same fixed candidate in the same executable context.
The existing warning-streak policy scaled only the wrapper-level executed
command and only while a naturally computed warning gate was open. The
nominal command, internal CBF-QP output, CBF-QP implementation, dynamics,
GSplat query, and planner remained unchanged.

## 4. Results

| Metric | Result |
| --- | ---: |
| `noop_steps_observed` | 70 |
| `noop_natural_warning_steps` | 11 |
| `noop_first_natural_warning_step` | 60 |
| `confirmed_natural_warning` | true |
| `active_smoke_attempted` | true |
| `active_steps_observed` | 69 |
| `active_natural_warning_steps` | 10 |
| `active_first_natural_warning_step` | 60 |
| `slowdown_active_steps` | 10 |
| `first_slowdown_step` | 60 |
| `activation_observed` | true |
| `slowdown_after_or_at_warning` | true |
| `min_scale_applied` | 0.25 |
| `max_scale_applied` | 0.75 |
| `max_control_delta_from_slowdown` | 0.018518980592489243 |
| `command_modified_only_when_warning` | true |
| `u_nom_modified` | false |
| `u_safe_internal_modified` | false |
| `wrapper_exec_command_scaled` | true |
| `collision_observed` | false |
| `qp_infeasible_observed` | false |
| `recovery_used_observed` | false |

The active scale range reports warning-gated active steps only. No release was
observed before this bounded active run terminated.

## 5. Interpretation

The active slowdown policy was exercised under naturally observed warning
conditions in the fixed C003 targeted smoke. This validates warning-gated
activation and wrapper-level command scaling in this fixed candidate only. It
does not establish performance improvement or benchmark superiority.

The no-op and active runs both first observed warning at step 60. Scaling began
at step 60, occurred on 10 warning steps, and never modified a command outside
the warning gate. The maximum deltas of `u_nom` and internal `u_safe` were both
exactly 0.0.

## 6. What Level 3B-Active Validates

For fixed C003 only:

* the previously reproduced warning context remained executable;
* warning-gated slowdown activated after a natural warning;
* slowdown timing did not precede warning timing;
* active scales stayed within the configured bounds;
* scaling occurred only on the wrapper-level executed command; and
* CBF-QP, dynamics, GSplat query, and planner code were not modified.

## 7. What Level 3B-Active Does Not Validate

* No full benchmark
* No safety performance improvement
* No collision reduction
* No warning reduction
* No planning accuracy improvement
* No planner integration
* No real-robot validation
* No global safety guarantee
* No new CBF theorem

## 8. Decision

Because `activation_observed=true`,
`command_modified_only_when_warning=true`, `u_nom_modified=false`, and
`u_safe_internal_modified=false`, Level 3B-Active is sufficient to consider a
Level 3C targeted A/B comparison on fixed C003 only. Do not broaden this result
to full100 or a benchmark claim.

SAFC fixed-candidate Level 3B-Active validates warning-gated slowdown activation
and wrapper-level command scaling only if `activation_observed=true`.

Active slowdown was exercised under naturally observed warning conditions in
fixed C003; this is targeted activation evidence, not benchmark performance
evidence.
