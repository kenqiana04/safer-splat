# L0 Start-Safe Failure Semantics Diagnosis V1

This task-local package diagnoses, without changing any V1 result, why all 14,122 committed states received typed L0 `FAIL` under the frozen current-state FULL-map query.

The implementation is internally consistent: it computes the minimum signed squared point-to-ellipsoid clearance over every loaded Gaussian and subtracts the frozen L0 effective radius squared once. The decisive contract mismatch is external to that formula. The frozen controller uses radius `0.015`, while shadow L0 uses robot radius `0.10` plus margin `0.01`, hence effective radius `0.11`.

Because source inspection alone could not prove the sign of the stored states, the preregistered 15-state sentinel set was locked before reading any `h`. The exact frozen L0 query returned negative `h` for all 15. Their pre-inflation clearance distances were `0.0265912–0.0739547`: every sentinel clears the controller radius but lies within the shadow L0 radius. This is diagnostic evidence only, not a cohort estimate.

Root class: `SS-F5 — L0_CONTROLLER_GEOMETRY_CONTRACT_MISMATCH`.

No controller, map, certifier, threshold, radius, margin, upstream artifact, formal row, rollout, or V1 scientific result was changed.
