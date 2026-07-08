# FC-Aware V1 Exact Recall Decision

- Exact recall audit success: yes.
- Target rows: 199.
- Best deployable: {"cap": 16000, "ranking_strategy": "nearest_first", "ranking_group": "deployable", "low_h_threshold": 0.01, "step_count": 199, "reduction_ratio_mean": 0.34287871488564525, "dual_active_recall_min": 1.0, "tight_recall_min": 1.0, "low_h_recall_min": 1.0, "combined_risk_recall_min": 1.0, "dropped_dual_active_total": 0, "dropped_tight_total": 0, "dropped_low_h_total": 0, "dropped_combined_risk_total": 0, "logging_runtime_mean": 0.06267664606809312, "logging_runtime_p95": 0.08566435594111672, "logging_runtime_max": 0.584384111687541, "candidate_for_wrapper_smoke": true}
- Best oracle: {"cap": 12000, "ranking_strategy": "low_h_active_hybrid", "ranking_group": "oracle", "low_h_threshold": 0.01, "step_count": 199, "reduction_ratio_mean": 0.5048772123538535, "dual_active_recall_min": 1.0, "tight_recall_min": 1.0, "low_h_recall_min": 1.0, "combined_risk_recall_min": 1.0, "dropped_dual_active_total": 0, "dropped_tight_total": 0, "dropped_low_h_total": 0, "dropped_combined_risk_total": 0, "logging_runtime_mean": 0.06267664606809312, "logging_runtime_p95": 0.08566435594111672, "logging_runtime_max": 0.584384111687541, "candidate_for_wrapper_smoke": false}
- Recommended action: `RECOMMEND_WRAPPER_LEVEL_CAPPED_CLOSED_LOOP_SMOKE_ONLY`.
- Reason: a deployable ranking met the recall thresholds with meaningful reduction on the recall audit
- Recommend continue FC-Aware V1: conditional on this action.
- Recommend wrapper-level capped closed-loop smoke: only if the recommended action says smoke; otherwise no.
- Recommend full100 now: no.
- Need better deployable score design: yes if oracle works but deployable does not, or if deployable recall is insufficient.
- Forbidden statements: do not claim a new CBF theorem, safety guarantee, runtime improvement, or closed-loop validation from this audit.
