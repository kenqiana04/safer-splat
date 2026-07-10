# SAFC Negative and Neutral Evidence Register

Negative and neutral results must remain visible and must not be omitted from
later paper preparation.

## Negative Evidence

### C004 Current-Policy Warning Increase

Level 3D reported C004 as the candidate where active slowdown increased warning
steps relative to baseline. Level 3E retained this negative evidence:
current_policy produced 68 warning steps while the Level-3D baseline reference
was 64.

### C004 Scale Sensitivity

Level 3E showed C004 warning steps of 68 under current_policy and 64 under both
milder_slowdown and critical_only_slowdown. This is diagnostic evidence that
the C004 behavior is scale-sensitive, not generalized improvement evidence.

### No Candidate Completed

No candidate completed in Level 3D. No candidate completed under any Level 3E
variant. This blocks any claim that warning-streak slowdown improves completion
or planner performance.

### Warning-Rich Discovery Limitations

The initial warning-rich discovery/reconciliation path showed that report-level
contexts cannot be assumed to reproduce directly as executable natural-warning
contexts. This motivated Level 3B-R and fixed-candidate testing.

### FC-Aware / MPC-Style Negative Results

Previously documented FC-Aware and primitive MPC-style recovery branches remain
diagnostic or future-work evidence. They should not be promoted into the final
method.

## Neutral Evidence

### C006 Equal Warning Counts

Level 3D reported C006 as neutral. Level 3E preserved this: current_policy,
milder_slowdown, and critical_only_slowdown all produced 41 warning steps.

### Collision and QP Infeasibility Counts

Level 3D and Level 3E reported zero collision and zero QP infeasibility counts
in the compared conditions. These zero counts do not prove generalized
improvement because the baseline and active conditions both had zero counts.

### Stop Reasons

The current policy did not improve stop reasons. In Level 3E, C003 remained
`stalled_before_goal`, while C004, C002, C001, and C006 reached `max_steps`
under every tested variant.

### Progress Proxy

The progress proxy is compact goal-distance reduction only. It is diagnostic
and must not be presented as completion, route quality, or planner quality.
