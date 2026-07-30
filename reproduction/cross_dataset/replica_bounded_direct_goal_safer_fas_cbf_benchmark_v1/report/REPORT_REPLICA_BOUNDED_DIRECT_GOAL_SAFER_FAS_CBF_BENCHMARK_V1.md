# Replica Bounded Direct-Goal SAFER and FAS-CBF Benchmark V1

**FINAL_STATUS:** `PASS_REPLICA_BOUNDED_DIRECT_GOAL_SAFER_FAS_CBF_BENCHMARK_COMPLETE`

**FINAL_DECISION:** `FREEZE_REPLICA_RESULTS_AND_PROCEED_TO_LEARNED_EXTERNAL_3DGS`

**Only next task:** `SCANNETPP_LEARNED_3DGS_EXTERNAL_QUALIFICATION_V1`

## Protocol integrity

- Identity SHA `902a699e52ca03de7f03d25b1d93c72f9b7b8afc263c1d123c1618e96811ba6b`; execution lock SHA `29b022dfabfa1c4fc5335d29034121f3be5732b961e61f209391d46a548ba619`.
- 500 unique terminal records plus markers; diagnostic=100, formal=400; five zero-step map-blocked records are retained.
- Post-lock code hash check=True; post-QP clip/fallback/map mutation/tuning and mesh-controller-input counters are all zero.
- GPU 1 task compute after completion: `none`.

## Scientific outcomes

| Method | all100 terminal | formal80 terminal | raw success | map-admissible success | collisions | min mesh clr. m | median progress m | p95 controller s | misses |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| M0_BOUNDED_SAFER | {'SUCCESS': 99, 'MAP_GEOMETRY_BLOCKED': 1} | {'MAP_GEOMETRY_BLOCKED': 1, 'SUCCESS': 79} | 0.9900 | 1.0000 | 0 | 0.0377 | 1.0137 | 0.0041 | 0 |
| M1_BOUNDED_RISK_AWARE_V1 | {'SUCCESS': 99, 'MAP_GEOMETRY_BLOCKED': 1} | {'MAP_GEOMETRY_BLOCKED': 1, 'SUCCESS': 79} | 0.9900 | 1.0000 | 0 | 0.0377 | 1.0137 | 0.0409 | 105 |
| M2_FAS_START_SAFE | {'SUCCESS': 99, 'MAP_GEOMETRY_BLOCKED': 1} | {'MAP_GEOMETRY_BLOCKED': 1, 'SUCCESS': 79} | 0.9900 | 1.0000 | 0 | 0.0377 | 1.0137 | 0.0409 | 134 |
| M3_FAS_START_SAFE_DISCRETE | {'SUCCESS': 99, 'MAP_GEOMETRY_BLOCKED': 1} | {'MAP_GEOMETRY_BLOCKED': 1, 'SUCCESS': 79} | 0.9900 | 1.0000 | 0 | 0.0377 | 1.0137 | 0.0409 | 116 |
| M4_FAS_START_SAFE_DISCRETE_RECOVERY | {'SUCCESS': 99, 'MAP_GEOMETRY_BLOCKED': 1} | {'MAP_GEOMETRY_BLOCKED': 1, 'SUCCESS': 79} | 0.9900 | 1.0000 | 0 | 0.0492 | 1.0137 | 0.0406 | 53 |

All 495 map-admissible trials succeeded; all 500 records had zero official-mesh collisions. Zero collision events do not justify a statistical safety-superiority claim.

## Start-Safe, verifier, recovery and Risk-Aware

- Static Start-Safe: 30 states, 30 accepted projections; in-trial projection applications=297.
- The exact segment verifier passed its two fresh-process preflight checks.
- M4 recovery triggers/successes/failures: 45/45/0.
- Risk-Aware binding SHA: `6e68525207a86bfebe0e463ea776f428453801861d9384be770c3ceed711a660`; its frozen source/config evidence is retained.

## Timing, statistics, and limits

- Controller time excludes mesh oracle and disk logging. Formal80 has nonzero deadline misses, hence `NO_REAL_TIME_CLAIM`.
- Paired analysis uses 10,000 bootstrap resamples (seed 20260730) and exact McNemar binary comparisons on 99 map-admissible route pairs.
- Large trajectories and step logs remain server-only; this package contains compact evidence.
- No learned training/search/download, SplaTAM rescue, ICP/Sim(3)/scale fitting, TUM work, route/map mutation, or controller tuning was performed.
