# FC-Aware V1 Exact Logging Feasibility Decision

## Status

Exact logging feasibility probe completed.

| item | status |
|---|---|
| read-only inspector | completed |
| dry-run probe | completed |
| no-intervention probe | completed |
| closed-loop run | no |
| full100 run | no |
| official core modified | no |

## Exactness

| field | decision |
|---|---|
| final candidate source IDs | exact |
| heading distance / cosine | exact |
| per-candidate `h` values | exact for final candidate set in wrapper replay |
| low-`h` IDs | exact under `h <= 0.01` in wrapper replay |
| active constraint IDs | exact for Clarabel dual-active rows in wrapper replay |
| active IDs proxy only | no for new probe; unavailable in old saved logs |

The active-ID definition is numerical and solver-specific: `dual z > 1e-7` mapped through the wrapper constraint-ID mapping. Tight constraints are separately logged with `abs(l - A @ u) <= 1e-7`.

## Probe Metrics

| metric | value |
|---|---:|
| written steps | 5 |
| dual-active count total | 10 |
| tight-active count total | 6 |
| low-`h` count total | 6951 |
| logging overhead mean | 0.095516 s/step |
| logging overhead p95 | 0.197346 s/step |
| logging overhead max | 0.230307 s/step |

The overhead is acceptable for an offline exact recall audit. It should not be reported as runtime improvement evidence.

## Decision

| question | answer |
|---|---|
| continue FC-Aware exact recall audit? | yes |
| recommend capped closed-loop smoke? | no |
| recommend full100 now? | no |
| freeze FC-Aware V1? | no, continue logging / recall audit only |
| paper positioning | diagnostic and future efficiency direction |

## Next Step

Run an exact recall audit over targeted risk-window rows using the newly feasible fields:

- retained heading top-M IDs by ranking strategy,
- active dual recall,
- tight-constraint recall,
- low-`h` recall,
- risk-window recall failures.

Do not run a capped closed-loop smoke until the recall audit identifies a defensible cap / ranking strategy. Do not run full100 until a smaller closed-loop smoke and flight20-scale evidence justify it.

## Wording Constraints

- Do not claim FC-Aware V1 improves runtime.
- Do not claim FC-Aware V1 is safe.
- Do not claim closed-loop validation.
- Do not call old saved-log active IDs exact.
- Do not describe `h` as meter clearance.
- Do not describe margin violation as collision.
