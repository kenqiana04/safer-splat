## Scope

Implements PR #96 (`1783aff5f6d221efc26d34f8b47b966e2d9eee3e`) as instrumentation-only infrastructure. PR #96 is Open Draft on `design-l2-h1-on-policy-shadow-observation-v1`; PRs #83/#84/#86/#87/#89/#90/#91/#92/#93/#94/#95/#96 remain read-only.

## Protected boundary and implementation

The 17 protected blobs pass raw blob/size/mode identity. `run.py` is supplemental protected controller evidence, so there is **no production delta** and no copied controller loop. The fallback outer `runpy` decorator wraps the imported frozen CBF and plant callables. Its tap occurs at entry to the exact frozen plant function, which is reachable only after the caller's success guard, and before delegation to the unchanged plant implementation.

`x_k/p_k/v_k/dt`, selected `u_k`, nominal `u_des`, reachability facts, provenance and `map_authority_id` become an immutable canonical payload. `u_des=NOMINAL_REFERENCE`; selected `u=SELECTED_EXECUTED_CONTROL`; genuine pre-observation siblings alone may be `NATIVE_SIBLING_CONTROL`. Synthetic candidate count is zero.

CPU/CUDA-like QA verifies independent device-to-host copy semantics and no source aliasing. Enqueue and worker-receive semantic hashes are equal. Static maps are hashed once at run start; steps carry only the stable authority ID.

The transport is bounded and `put_nowait`. Queue full, worker unavailable/crash, serialization error, map failure and bounded shutdown affect instrumentation health only. The worker writes append-only capture/result/health logs and exposes no result-return channel. L0/L1 are explicitly shadow recomputations; instrumentation failures never become L2 `UNKNOWN`.

## QA and claims

F1-F10 task-local fault injection passes with unchanged deterministic mock controller traces. Four reviewers vote Case A. Real OFF-vs-ON navigation equivalence, logging pilot, formal cohort, runtime benchmark and performance benchmark were **NOT RUN**. No controller efficacy, collision reduction, progress, recursive feasibility, real-time or deployment claim is made.

**Selected Case:** `CASE_A_FAITHFUL_NONINVASIVE_INSTRUMENTATION_IMPLEMENTED`

**FINAL_STATUS:** `PASS_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_IMPLEMENTATION_V1`

**FINAL_DECISION:** `FREEZE_INSTRUMENTATION_AND_VALIDATE_OFF_VS_ON_CONTROL_TRACE_EQUIVALENCE`

**Only next task:** `VALIDATE_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1`
