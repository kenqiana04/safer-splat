# Future proof obligations and design discharge

These are architectural obligations; `DESIGN_PASS` means the written route/certificate contract excludes an unsafe edge, **not** that runtime implementation or GPU evidence has passed.

| ID | Obligation | Design discharge / future test |
|---|---|---|
| PO1 | No recovery action without full chain | C0→L2→canonical L3 PASS+bundle→Supervisor; C02/C05/C06 |
| PO2 | Hard geometry unchanged | registry 0.015 q, margin/rho 0, epsilon NONE; static diff gate |
| PO3 | Cert/execution identity exact | canonical predicted/actual identity; C07/C08/C16 |
| PO4 | L1 facts immutable | once-per-cycle L1 result, fresh attempt binding |
| PO5 | Future control authority causal | ∂p(k+1)/∂u=0, ∂p(k+2)/∂u=dt²I; C17/C18 |
| PO6 | Valid retained backup preserved | C01, frozen backup priority |
| PO7 | Stale backup never resurrected | store.validate exact identity; C11 |
| PO8 | Terminal/boundary from every local failure | prefetched exact terminal; C03–C06/C09/C10 |
| PO9 | Exact-one Supervisor routing | disjoint mode/backup/deadline/status guards; static fixture lookup |
| PO10 | Coordinator never selects action | only executes Supervisor destination |
| PO11 | UNKNOWN never automatic retry | global/unresolved UNKNOWN typed boundary; C04 |
| PO12 | One trace per public cycle | reuse ActiveRunner outcome path and additive fields |
| PO13 | No infinite internal search | six candidates maximum and numeric-state exhausted key; C13 |
| PO14 | Primary re-entry fresh certified | next cycle starts L1/P0/C0/L2/L3; C12 |
| PO15 | Historical 0.025 no authority | registry/source audit; C15 |
| PO16 | No progress/NI runtime trigger | only typed certificate/backup/deadline/identity facts |
| PO17 | No hidden global planner | six fixed axis-bound local vectors; no waypoints/search graph |
| PO18 | Deadline semantics preserved | OPEN admits work; WARNING/EXPIRED stop new search; C09/C10 |
| PO19 | No hard real-time claim | time checks are routing guards, not latency guarantee |
| PO20 | Frozen verdicts immutable | input hashes and task-only Git diff; no reanalysis |

Any implementation failure of one obligation blocks smoke and preserves the frozen terminal/boundary path. No proof obligation is discharged by the existing 85-pair efficacy data.
