# REPORT — Diagnose L0 Start-Safe Failure Semantics V1

## Answer first

1. **Exact `h` contract.** For Gaussian `i`, frozen code computes local coordinates `q_i=R_i^T(p_k-mu_i)`, the closest ellipsoid point, squared clearance `d_i^2`, inside/outside sign `phi_i=sign(sum((q_i/s_i)^2)-1)`, then `h_i=phi_i d_i^2-r_eff^2`. FULL query returns `h(p_k)=min_i h_i` over all loaded Gaussians.
2. **Sign convention.** Consistent: finite `h>=0` is PASS, finite `h<0` is FAIL, nonfinite is UNKNOWN.
3. **Radius/margin accounting.** Shadow L0 combines `0.10 + 0.01` once into `r_eff=0.11` and subtracts `0.11^2=0.0121` once. No duplicate L0 inflation was found.
4. **Frame/scale verdict.** CONSISTENT. `p_k=state[:3]` is queried directly in the same map coordinate system; Gaussian log-scales are exponentiated once; no duplicate state/map transform or normalization is present.
5. **Map obstacle semantics verdict.** FULL query includes every loaded Gaussian; opacity and semantic obstacle filtering are absent. The controller uses the same checkpoint, Gaussian set, and filtering behavior. Whether checkpoint Gaussians semantically label floor/background is not established by source metadata.
6. **L0 versus controller verdict.** PARTIALLY_EQUIVALENT. State point, map, Gaussian set, ellipsoid math, aggregation, and sign match, but controller radius is `0.015` while shadow L0 effective radius is `0.11`.
7. **Sentinel executed.** Yes, because static code could identify the radius mismatch but could not establish stored-state clearances without raw `h`.
8. **Sentinel result.** Fixed 15 existing states: `h` min/median/max = `-0.0113929091 / -0.0103109423 / -0.00663070148`; all negative. Their pre-inflation clearance distances are `0.0265912–0.0739547`.
9. **Root class.** `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`.
10. **One-sentence explanation.** 14122 L0 FAILs are best explained by a 0.11 shadow-L0 versus 0.015 frozen-controller radius contract mismatch on the same Gaussian clearance field; no V1 result is changed.

## Frozen evidence boundary

The direct upstream is PR #104, Open Draft branch `diagnose-l0-shadow-certifier-semantics-v1`, exact head `14c844adeda8a0e8eb418abcdbaac62c701e2910`. Its compact lock and summaries establish 14,122 formal rows, 14,122 typed L0 FAIL, zero PASS, zero UNKNOWN, and reason `FROZEN_L0_CURRENT_MAP_QUERY`. Raw `h` was not logged. L0 queried current `p_k`, did not inspect the immediate segment or candidate control, did not invoke repair, and affected only the shadow observation closure after the production action had already committed.

This diagnosis is post hoc. It does not change those facts, reconstruct all 14,122 values, rerun any trial, or write sentinel values back into formal evidence.

## Mathematical and implementation evidence

The frozen Nerfstudio loader copies means and quaternions, exponentiates the learned log-scales once, constructs covariance matrices, and loads sigmoid opacities (`splat/gsplat_utils.py:31-40`). The ball-to-ellipsoid path transforms `p_k` into each Gaussian frame, computes the closest ellipsoid point, assigns an inside/outside sign, and forms `phi*d^2-(radius+epsilon)^2` (`splat/gsplat_utils.py:162-185`). The underlying solver returns `sum((y-x)^2)` (`splat/distances.py:96-130`), so the executed computation consistently uses squared distance and squared radius.

The source adapter calls this query with `effective_radius`, rejects any nonfinite array as `NONFINITE`, and selects the minimum finite element by `argmin` (`gaussian_barrier_adapter.py:87-97`). The formal L0 maps that finite minimum to PASS for `h>=0`, otherwise FAIL (`server_run_one.py:165-170`). Formula sign and status sign therefore agree.

The zero set is the boundary of the union of radius-inflated represented ellipsoids. Positive `h` means the point lies beyond the effective radius from every represented ellipsoid; zero is contact; negative means the point is inside an ellipsoid or within the effective radius of at least one.

## Frame, scale, and state reference

The immutable payload copies `state[:3]` into `p_k` and `state[3:]` into `v_k` (`immutable_payload.py:170-173`). L0 passes `p_k` directly to the FULL query. The controller likewise passes `x[..., :3]` to the same map query (`cbf/cbf_utils.py:45`). There is no camera/body conversion, world/map normalization, axis reorder, or duplicated pose transform between either point and the map. Only the expected per-Gaussian local transform `R_i^T(p-mu_i)` occurs.

The map authority contract expresses robot radius and margin in metres; the same runtime state and Gaussian checkpoint are consumed by controller and shadow L0. No evidence supports a metre-versus-normalized-unit defect, sensor-origin substitution, or duplicated transform.

## Represented-map obstacle semantics

The FULL path evaluates all 116,446 Gaussians loaded from the frozen Stonehenge map in the sentinel run. Although opacity is loaded, it is not used by this query. There is no obstacle-class, floor, support-surface, background, opacity, or top-k filter. Therefore any such reconstruction Gaussian present in the checkpoint participates in the union minimum.

That fact does not distinguish L0 from the frozen controller: both use the same map and unfiltered query. Consequently, source evidence does not support `SS-F4` as the immediate cause. It also does not establish whether every included Gaussian should operationally be called an obstacle; that semantic question remains explicitly outside the present root classification.

## Controller versus shadow L0 contract

The runtime runner freezes the same Stonehenge configuration for controller and L0, but records `controller_radius=0.015` (`server_run_one.py:340`). Shadow authority separately records robot radius `0.10`, safety margin `0.01`, and effective radius `0.11` (`server_run_one.py:101-103,125-127`). The radius ratio is `7.3333`; the squared inflation term ratio is `53.7778`.

Thus the same raw signed squared clearance `c(p)` is interpreted as:

- controller geometry: `h_controller = c(p) - 0.015^2`;
- shadow L0 geometry: `h_L0 = c(p) - 0.11^2`.

This is not an L0-internal double subtraction. It is a mismatch between two frozen geometry authorities.

## Bounded sentinel reconstruction

Static evidence established the mismatch but not where the stored states lay relative to both radii. Before reading any `h`, the task locked trials `[0,24,49,74,99]` and, per trial, the first, `floor((N-1)/2)`, and last committed step. The lock stores exact trial/step identifiers, state hashes, decision commit IDs, map authority, map/config identity, query source hashes, and radius/margin values. Sample count is exactly 15.

One offline batch reused the frozen checkpoint, frozen FULL query, frozen `0.11` radius, and original states. It launched no rollout and left no GPU process. Results:

| Diagnostic quantity | Result |
|---|---:|
| n | 15 |
| L0 h min | -0.0113929091021 |
| L0 h median | -0.0103109423071 |
| L0 h max | -0.00663070147857 |
| all h negative | true |
| raw squared clearance min | 0.000707090897858 |
| raw squared clearance median | 0.00178905769289 |
| raw squared clearance max | 0.00546929852143 |
| raw clearance distance min | 0.0265911808 |
| raw clearance distance median | 0.0422972540 |
| raw clearance distance max | 0.0739547059 |

All 15 raw clearances exceed `0.015^2=0.000225` and remain below `0.11^2=0.0121`. Therefore each bounded sentinel is outside the controller-radius zero set but inside the shadow-L0 zero set under the shared raw clearance field. No second radius query or parameter sweep was performed; the comparison uses the raw component returned by the same frozen L0 computation.

These 15 points are deterministic sentinels, not a random or representative cohort sample. They support the mechanism and sign reproduction only. They do not estimate the distribution, prevalence, quantiles, or uncertainty of all 14,122 rows.

## Root classification and alternatives rejected

Selected: `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`.

- `SS-F1` rejected: formula and status sign agree.
- `SS-F2` rejected: no frame, transform, axis, or metric-scale mismatch was found.
- `SS-F3` rejected: L0 combines radius and margin once and subtracts the resulting square once; the defect is cross-contract radius disagreement, not repeated L0 inflation.
- `SS-F4` not selected: FULL all-Gaussian semantics are shared with the controller; semantic floor/background labels are unavailable.
- `SS-F6` not selected: the sentinel raw clearances show that the negative result depends on the larger shadow radius rather than being negative under the controller's own radius.

The conclusion is deliberately bounded: the radius mismatch is the best directly supported explanation for the systematic typed FAIL pattern. Because formal raw `h` is absent and only 15 locked sentinels were reconstructed, this report does not claim an all-row clearance distribution.

## Validation and next boundary

Six task-local tests cover sign, radius/margin accounting, frame transform direction, deterministic sentinel selection, status/sign mapping, and mutation-path isolation. The validator checks exact PR #104 identity, upstream locks, frozen counts, source evidence in each audit, the conditional sentinel gate, `n<=15`, zero rollout, task-local-only mutation, and absence of raw map/log/full-table artifacts.

Final status: `PASS_L0_START_SAFE_FAILURE_SEMANTICS_DIAGNOSIS_V1`.

Final decision: `FREEZE_L0_FAILURE_MECHANISM_AND_AUTHORIZE_MINIMAL_TARGETED_NEXT_STEP`.

Only next task: `DESIGN_L0_CONTROLLER_GEOMETRY_CONTRACT_V2`.

That next task must first decide the intended shared geometry authority. This task does not authorize changing L0, the controller, the threshold, map filtering, robot radius, safety margin, or any V1 result.
