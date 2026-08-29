# L2/H1 shadow instrumentation OFF-vs-ON equivalence V1

This task is a bounded deterministic QA experiment, not a safety-efficacy, performance, logging-completeness, or prospective-cohort study.

It runs three serial fresh-process arms against the exact frozen Stonehenge controller:

- `NATIVE_OFF`: no PR #97 wrapper and no observer.
- `WRAPPER_OFF`: exact PR #97 wrapper loaded and delegated, observer disabled, no worker.
- `WRAPPER_ON`: exact PR #97 wrapper plus immutable capture, canonical hashes, map authority, bounded nonblocking queue, worker, frozen L0/L1/L2 observation, and append-only evidence logs.

The preregistered primary outcome is canonical exact equality of the stepwise frozen control trace. Shadow certificate results have zero authority and do not enter trial selection or the equivalence decision.

## Result

`PASS_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1`

- 21 real QA navigation runs: 7 per arm.
- A/B/C self-consistency: exact for every arm.
- Frozen cross-arm trials: `0, 24, 49, 74, 99`.
- A/B, B/C, and A/C: 5/5 exact for each pair.
- First divergence: none.
- Arm C: 1,490 captures and 1,490 joined results; zero authority, intervention, replacement, or leftover worker.

The full bounded interpretation is in `report/REPORT_VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1.md`. The next task is not authorized or executed here.
