# TUM SplaTAM G1 Boundary-Event and Discrete-Time Forensics V1

## Result

`PASS_TUM_G1_TRUE_SAMPLED_DATA_OVERLAP_CERTIFIED` (Case C) and
`DT_PRECURSOR_DETECTED`.

This is a certification of the frozen PR #47 GSplat geometric-overlap proxy,
not a mesh-collision result or a safety theorem.  It changed neither the
original controller nor its state/control sequence.

## Frozen identity and run boundary

- PR #47 base head: `5f3078a88ba6121ba2c1918a1b89120438006916`.
- Authoritative server checkout: `f63b4c496861c4f8881348d74244c1ff9a528d51`;
  all three required source blobs matched.
- Canonical SplaTAM map: 5,464,102 Gaussians; transforms SHA-256:
  `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Frozen original trial: frame 0 to 50, radius 0.015, alpha/beta 5/1,
  `dt=0.05`, 800-step cap, tolerance 0.001.
- Original record: terminal step 773, progress `0.6442182910871558`, official
  float32 minimum h `-7.421476766467094e-10`, no QP infeasibility and no
  nonfinite state.  The initial pair was safe (`h=6.717070937156677e-05`).
- No deterministic rerun was needed.  The frozen safe controls deterministically
  reconstruct the state sequence (state SHA-256
  `e73a41bb8024d6b02af0d72cc69bd19df10a190ec8de0aacddc3f2d3e5a50f38`).

## Runtime and evidence recovery

The recovered runtime transition is explicit Euler (case A):

`p_next = p + dt*v`, `v_next = v + dt*u`.

Replaying all 773 logged safe controls gives zero difference from the recovered
state sequence.  The PR #47 steps log did not independently store every state,
so this validates deterministic reconstruction rather than certifying a
separate logged-state comparison.  The diagnostic alternative
`p_next=p+dt*v+0.5*dt^2*u` differs by up to `0.001250760808232873` and was not
substituted for runtime behavior.

The fixed event window was steps 740--773.  Full-map queries were run for all
available `x_k` and `x_{k+1}` records (67 state queries; no `x_774` exists
because the frozen run stopped at 773).  At 773 the full-map active source
index was `4610535`, with no exact float32 tie and a preserved top-32 list in
server evidence.

There is no original spatial pre-query candidate filter: the frozen
`cbf/cbf_utils.py` calls complete-map `GSplatLoader.query_distance` before its
post-query `h_rep_minimal` QP-polytope reduction.  Consequently every event
window query used all 5,464,102 candidates; certified filter-miss count is 0.

## Independent float64 boundary reference

Both independent raw-geometry solvers used canonical float64 means, axes,
quaternions, query position, and radius 0.015.  Reference A is safeguarded KKT
bisection; Reference B is safeguarded Newton with bisection fallback.  Neither
uses the official float32 root solver or Hessian implementation.

| quantity | value |
| --- | ---: |
| step 772 h_ref | `9.879318122580326e-10` (ROBUST_SAFE) |
| step 773 h_ref A/B | `-3.406563170113043e-10` / `-3.406563170113043e-10` |
| tau_ref | `1e-12` |
| max KKT/surface residual | `2.220446049250313e-16` |
| official float32 h | `-7.421476766467094e-10` |
| official minus reference | `-4.0149135963540514e-10` |

Thus the predecessor was robustly safe and the terminal point robustly
overlapped, with first robust overlap at 773.  This certifies a sampled-data
one-step crossing, not a float32 sign false positive, pre-QP unsafe state,
filter miss, or integration-log mismatch.

## Shadow-only H1/H2/H3 audit

The recovered frozen source is SHA-256
`f2545ad2ea593e44e70d29979dad609bb7c1ecf7fa1d538baebce01c6a6417d6`.
H1/H2/H3 mean respectively one, two, and three explicit-Euler future steps
while holding the logged `u_safe[k]` fixed.  They use the historical
`dt_margin=0.0005`, complete-map query semantics, and do not modify any state,
control, QP, or recovery behavior.

| verifier | warnings | first warning | minimum predicted h | warning at k=772 |
| --- | ---: | ---: | ---: | --- |
| H1 | 384 | 0 | `-7.421476766467094e-10` | yes |
| H2 | 385 | 0 | `-1.8480932340025902e-09` | yes |
| H3 | 386 | 0 | `-2.7794158086180687e-09` | yes |

The earliest historical margin warning is H1 at step 0 (773 steps / 38.65 s
before the robust event), but 383 H1 warnings are nonnegative margin warnings.
The meaningful immediate precursor is the H1 warning at step 772 predicting
the terminal overlap.  These are margin warnings, not collisions; the audit
does not claim that DT verification avoided the event.

State and safe-control input hashes stayed identical before and after shadow
instrumentation.  No Start-Safe, Risk-Aware controller, predictive recovery,
20/100-trial benchmark, formal training, or V1R7 was run.

## Claim boundary and next task

The original PR #47 result remains preserved as
`TUM_SPLATAM_G1_COLLISION_STOP`; this report only adds the numerical meaning of
its terminal GSplat proxy.  A separately authorized intervention experiment
would need a new preregistered controller/verification protocol and must not
reuse or mutate this frozen baseline.
