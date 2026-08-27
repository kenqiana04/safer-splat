# Control-Flow Observation Seam Audit

**Scope label:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.

## Frozen production cycle

The audit uses source at PR #95 head `a7fd936804284a299467f1bfcc76deab12fdf0c3` rather than old reports.

| Required item | Frozen source of truth | Finding |
|---|---|---|
| `x_k` | `run.py:101-104,116` | Six-vector tensor `x` exists before each control decision. |
| `p_k` | `run.py:119` and state convention at `run.py:100` | `x[:3]`. |
| `v_k` | `run.py:123,125` and state convention at `run.py:100` | `x[3:]`. |
| nominal candidate | `run.py:118-127` | `u_des` is the native PD candidate, clipped to the frozen bounds. |
| selected candidate | `run.py:132`; `cbf/cbf_utils.py:125-143` | `u = cbf.solve_QP(x,u_des)`; successful solver output is the selected control. |
| decision acceptance | `run.py:138-143` | The solver-success guard rejects the failed path. |
| decision commit seam | between `run.py:143` and `run.py:147` | After success and before plant update, `x_k`, `u_k`, `u_des`, `dt`, trial and step are co-resident and unambiguous. |
| plant application | `run.py:147` | `x = double_integrator_dynamics(x,u)*dt + x`. This is after the proposed capture. |
| current logging | `run.py:149-152,184-196` | `u` is appended only after propagation; capture here risks state/action misalignment and does not expose reachability IDs. |
| `dt` | `run.py:19`; serialized at `run.py:207` | Runtime authority is the module constant `0.05`; future manifest also hashes the config source. |
| trial/step | `run.py:98,116` | Deterministic `trial` and `i`; future instrumentation creates stable run/trial/step and commit IDs. |
| map object | `run.py:52,79`; `cbf/cbf_utils.py:10-38` | Stonehenge config reference enters `GSplatLoader`, then the CBF. Path alone is insufficient; future run-start manifest must hash the resolved config/checkpoint. |

## Frozen safety-stage sources

The primary `run.py` controller does **not** natively execute the PR #84 L0/L1 state machine. Therefore the design must not relabel QP success as stored L1. The future zero-authority worker will use the frozen PR #84 interfaces on the captured payload and record explicit stage reachability at evaluation time:

- current-feasibility/L0 observation: `reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/current_feasibility_certificate.py:8-22`;
- immediate-segment/L1 observation: `.../certifier/segment_certificate.py:10-18`;
- immutable `State`, `Control`, map snapshot and result types: `.../certifier/result_types.py:64-86,95,134-159,194-208`;
- frozen ordered candidates and unified stage progression: `.../certifier/executable_safety_certifier.py:25-80` and `.../certifier/candidate_library.py:8-18`;
- L2/H1 formula and tri-state result: `reproduction/shadow/l2_h1_shadow_certifier_v1/l2_h1_shadow_certifier.py`.

The worker's stored L0/L1/L2 values are labeled `SHADOW_PIPELINE_RUNTIME_OBSERVATION`, never `PRODUCTION_CONTROLLER_DECISION`. This removes post-hoc reachability guessing while preserving the controller's mathematics.

## Candidate lifecycle

The production baseline exposes two genuine native values before the shadow tap: nominal `u_des` and successful selected `u`. Both existed before observation. If they differ, the candidate group contains both with roles `NOMINAL_NATIVE` and `SELECTED_EXECUTED`; if identical, de-duplicate by hash while retaining both roles. No B3 candidate is synthesized.

The richer frozen PR #89 audit runtime forms a filtered primary at `source_runtime.py:153-159`, computes current and segment outcomes at lines 170-183, forms directional alternatives at lines 185-186, and commits a candidate at lines 187-195. This proves a native multi-candidate lifecycle can be tapped when that controller already creates one. However PR #89's returned record omits the final acceleration even though `control` exists internally; this is an exact cause of future replay loss. The future tap copies it before serialization.

## Selected seam decision

Seam `S1_AFTER_ACCEPT_BEFORE_PROPAGATE` is feasible and selected. It sees the correct `x_k/u_k/dt`, cannot confuse `x_(k+1)` with `x_k`, and requires only an instrumentation-only immutable copy plus nonblocking enqueue in the future task. The shadow worker has no callable return path. No source is changed in this design task.
