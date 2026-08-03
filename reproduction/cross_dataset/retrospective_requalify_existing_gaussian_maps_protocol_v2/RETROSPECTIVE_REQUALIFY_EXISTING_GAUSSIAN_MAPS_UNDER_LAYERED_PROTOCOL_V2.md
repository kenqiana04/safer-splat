# Retrospective Requalify Existing Gaussian Maps Under Layered Protocol V2

This task applies the immutable Protocol V2 from PR #75 to eleven existing map identities. It is a read-only, control-first requalification and cannot retrain, filter, repair, align, rescale, delete frames, alter historical routes, run controllers or planners, or introduce candidate-dependent alpha values, unknown models, routes, or numeric gates.

The fixed order is REPLICA_GT_FINE, REPLICA_SPLATFACTO, TUM_SPLATFACTO_NEGATIVE, REPLICA_SPLATAM_60, ARKITSCENES_M1_SPLATAM, TUM_SPLATAM_FORMAL, TUM_GAUSSIAN_SLAM, followed by the four official SAFER interface references. Candidate evaluation is authorized only after the positive control reaches R3/N3 and the executable negative control remains below N3.

The reconstruction axis is restricted to R0-R3; the navigation axis is restricted to N0-N3. `SAFETY_QUERY_COMPATIBLE`, `UNKNOWN_MODEL_STATUS`, and `REFERENCE_AUTHORITY` are independent fields. `UNKNOWN != FREE`; finite G0 cannot raise the navigation axis; empirical percentiles are not certificates; camera-ray evidence cannot establish full-space completeness.

Historical results remain valid under their historical contracts. Protocol V2 adds a task-specific evidence classification and never rewrites PR #68-#75.
