# FC-Aware V1 Exact Recall Positioning Update

FC-Aware V1 remains an efficiency-support candidate selection module around the official SAFER-Splat style CBF-QP pipeline. It does not replace Start-Safe CBF, discrete-time verification, CBF-QP filtering, or optional predictive recovery.

Exact recall audit action: `RECOMMEND_WRAPPER_LEVEL_CAPPED_CLOSED_LOOP_SMOKE_ONLY`.
Best deployable summary: {"cap": 16000, "ranking_strategy": "nearest_first", "ranking_group": "deployable", "low_h_threshold": 0.01, "step_count": 199, "reduction_ratio_mean": 0.34287871488564525, "dual_active_recall_min": 1.0, "tight_recall_min": 1.0, "low_h_recall_min": 1.0, "combined_risk_recall_min": 1.0, "dropped_dual_active_total": 0, "dropped_tight_total": 0, "dropped_low_h_total": 0, "dropped_combined_risk_total": 0, "logging_runtime_mean": 0.06267664606809312, "logging_runtime_p95": 0.08566435594111672, "logging_runtime_max": 0.584384111687541, "candidate_for_wrapper_smoke": true}
Best oracle summary: {"cap": 12000, "ranking_strategy": "low_h_active_hybrid", "ranking_group": "oracle", "low_h_threshold": 0.01, "step_count": 199, "reduction_ratio_mean": 0.5048772123538535, "dual_active_recall_min": 1.0, "tight_recall_min": 1.0, "low_h_recall_min": 1.0, "combined_risk_recall_min": 1.0, "dropped_dual_active_total": 0, "dropped_tight_total": 0, "dropped_low_h_total": 0, "dropped_combined_risk_total": 0, "logging_runtime_mean": 0.06267664606809312, "logging_runtime_p95": 0.08566435594111672, "logging_runtime_max": 0.584384111687541, "candidate_for_wrapper_smoke": false}

Safe paper wording:

- Heading-candidate dominance was identified as the main candidate-count bottleneck.
- Exact no-intervention replay can quantify active, tight, and low-h recall under hypothetical heading caps.
- Oracle rankings provide diagnostic upper bounds and motivate future deployable score design when deployable rankings lag.

Do not claim:

- FC-Aware V1 alone guarantees safety.
- The recall audit is closed-loop validation.
- The recall audit demonstrates runtime improvement.
- Oracle rankings are deployable.
- h or min_safety_h is metric clearance.
