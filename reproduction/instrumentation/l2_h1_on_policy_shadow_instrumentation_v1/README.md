# L2/H1 on-policy shadow instrumentation V1

This directory implements the PR #96 design as **instrumentation infrastructure only**. It does not contain on-policy research data, a navigation result, or a performance claim.

## Chosen implementation

`run.py` is read-only protected controller evidence, so the direct source hook is not used. `run_with_shadow_instrumentation.py` provides the approved fallback: it temporarily decorates the imported frozen `CBF` and plant functions. The CBF wrapper delegates the exact `solve_QP` and returns the exact selected object; immutable capture occurs only when the protected caller reaches the plant function after its success guard, immediately before delegating the unchanged plant.

The capture is a frozen dataclass/tuple snapshot. Tensor-like inputs are detached and copied to independent CPU storage before a bounded `put_nowait`. The worker has one inbound queue and append-only logs; it has no result-return API. `u_des` is always `NOMINAL_REFERENCE`; without genuine pre-existing siblings, native group size is one.

Map authority is content-addressed once per run. L0/L1 are labeled `SHADOW_RECOMPUTED_FROZEN_CERTIFIER`; instrumentation failures are health events and never L2 `UNKNOWN`.

## QA boundary

- 10 task-local F1-F10 fault cases: `PASS_F1_F10_ZERO_AUTHORITY_FAULT_QA`
- Real navigation equivalence: **NOT RUN**
- Logging pilot: **NOT RUN**
- Formal on-policy cohort: **NOT RUN**
- Controller/production source delta: **NONE_REQUIRED**

## Decision

`PASS_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_IMPLEMENTATION_V1`

Only the separately authorized next task may run real OFF-vs-ON control-trace equivalence.
