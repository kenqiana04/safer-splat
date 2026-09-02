# Legacy Evaluation Semantics Audit V2

Static evidence at PR #113 head:

- **EVAL-A:** `run.py:145-161` propagates the selected action, then calls `gsplat.query_distance(x, radius=radius, distance_type='ball-to-ellipsoid')` and records `min(h)`. It uses the represented Gaussian map/query family also used by the method. This is a method-map-relative endpoint diagnostic, not an independent final collision oracle.
- **EVAL-B:** `run.py:163-178` records explicit goal success only when the stalled pre-propagation 6-D state satisfies `||x_ - goal||_2 < 0.001`, but separately labels a moving timeout as success. V2 bans timeout-only goal success.
- **EVAL-C:** the legacy safety log checks post-step points only; it does not certify every closed executed segment. It can miss between-endpoint penetration and is not the V2 swept oracle.

Verdict: `LEGACY_RUN_PY_NOT_AUTHORIZED_AS_FINAL_V2_EVALUATION_ORACLE`. Historical outputs retain their historical meaning and are not rewritten.
