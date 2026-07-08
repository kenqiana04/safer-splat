# FC-Aware V1 Exact Logging Feasibility Probe

## 1. Purpose

This report checks whether FC-Aware V1 has the logging prerequisites needed for an exact recall audit.

It is a feasibility / instrumentation probe only. It is not capped closed-loop validation, not full100, not a runtime claim, and not a safety guarantee.

## 2. Background

Selected_K-only Adaptive V1 is risk-responsive, but it did not produce candidate-count or runtime reduction evidence because forced heading candidates dominate the final candidate union.

The FC-Aware heading shadow audit showed large theoretical reduction headroom, and the per-candidate source audit showed that source IDs can be reconstructed exactly. However, the saved logs did not contain exact active constraint IDs or per-candidate `h` values, so active / low-`h` recall was unavailable and no heading cap could be recommended.

This probe asks whether the missing exact fields can be logged without modifying official SAFER-Splat source.

## 3. Read-Only Inspection

Inspector outputs:

- `work/risk_aware_cbf/results/fc_aware_v1_exact_logging_feasibility/exact_logging_feasibility.md`
- `work/risk_aware_cbf/results/fc_aware_v1_exact_logging_feasibility/exact_logging_feasibility.json`

Summary:

| field | status |
|---|---|
| final candidate source IDs | reconstructable exact |
| heading distance / cosine | reconstructable exact |
| candidate `h` values | wrapper-feasible |
| low-`h` IDs | wrapper-feasible if `h` values are captured |
| active IDs in saved logs | unavailable |
| active IDs through wrapper dual capture | feasible |
| official core source modification required | no |

The official CBF solver path returns only the primal solution and success flag. The worktree wrappers already preserve candidate / constraint ID mapping, so a wrapper-only replay can capture Clarabel dual/slack values and map solver-active rows back to global Gaussian IDs.

## 4. No-Intervention Probe

Dry-run:

- command selected 5 input rows from targeted trials `12,13`,
- no GSplat load,
- no QP replay,
- no controller output used.

No-intervention replay outputs:

- `work/risk_aware_cbf/results/fc_aware_v1_exact_logging_feasibility/probe/exact_logging_probe_steps.jsonl`
- `work/risk_aware_cbf/results/fc_aware_v1_exact_logging_feasibility/probe/exact_logging_probe_summary.csv`
- `work/risk_aware_cbf/results/fc_aware_v1_exact_logging_feasibility/probe/exact_logging_probe_metrics.json`

Probe scope:

| item | value |
|---|---:|
| target trials | `12,13` |
| written steps | 5 |
| closed-loop run | false |
| full100 run | false |
| controller output used | false |
| candidate selection changed | false |
| official core modified | false |

Probe metrics:

| metric | value |
|---|---:|
| candidate IDs exact | true |
| heading scores exact | true |
| candidate `h` values exact | true |
| low-`h` IDs exact | true |
| active IDs exact | true |
| active IDs proxy only | false |
| dual-active count total | 10 |
| tight-active count total | 6 |
| low-`h` count total | 6951 |
| logging overhead mean | 0.095516 s/step |
| logging overhead p95 | 0.197346 s/step |
| logging overhead max | 0.230307 s/step |

Active IDs are defined in this probe as Clarabel dual-active constraint rows with `dual z > 1e-7`, mapped to global Gaussian IDs through the wrapper constraint-ID mapping. Tight IDs use `abs(l - A @ u) <= 1e-7`. These are solver replay logging fields, not fields that existed in the earlier saved logs.

Low-`h` IDs are exact for the final candidate set under the declared threshold `h <= 0.01`. The `h` value is the repository GSplat ellipsoid safety value, not meter clearance.

## 5. Exactness Decision

| question | answer |
|---|---|
| candidate source IDs exact? | yes |
| heading distance / cosine exact? | yes |
| candidate `h` values exact? | yes, for the final candidate set in wrapper replay |
| low-`h` IDs exact? | yes, for the declared threshold in wrapper replay |
| active IDs exact? | yes, for solver dual-active rows in wrapper replay |
| active IDs proxy only? | no for this probe; old saved logs remain unavailable |

## 6. Decision

| decision item | decision |
|---|---|
| continue FC-Aware exact recall audit? | yes |
| recommend capped closed-loop smoke now? | no |
| recommend full100 now? | no |
| freeze FC-Aware V1 now? | no; continue logging / exact recall audit only |
| paper positioning | diagnostic and future efficiency direction until recall and closed-loop evidence exist |

Because active IDs and low-`h` IDs are both obtainable in a wrapper-only no-intervention replay, the next defensible step is an exact recall audit over the targeted risk-window rows. This still does not justify a capped closed-loop smoke by itself. A cap/ranking strategy must first show high active and low-`h` recall.

## 7. Limitations

- This was not a capped closed-loop run.
- This was not a full100 benchmark.
- This did not enable V4-C recovery.
- This did not modify official core source.
- This does not prove safety.
- This does not claim runtime improvement.
- Solver-active IDs are numerical dual-active IDs under a declared tolerance.
- Existing historical logs still do not contain exact active / low-`h` fields.
- `h` / `min_safety_h` is a repository GSplat ellipsoid safety value, not metric clearance.
- A margin violation is not a collision.
