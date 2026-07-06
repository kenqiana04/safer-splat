# Adaptive V1 Targeted DT-Risk Closed-Loop Design

## 1. Purpose

This task runs a targeted DT-risk closed-loop diagnostic for Adaptive V1 balanced. It is not a full100 benchmark and not an official benchmark result.

## 2. Motivation

The flight20 closed-loop pilot established that `selected_K` was applied to V1 candidate budgeting, collision / QP / crash counts did not increase, and DT-warning / low-margin steps triggered balanced mode switching. It also showed that final measured candidate count barely changed because forced candidates dominated the selector output: `forced_candidate_fraction_mean=1.0` and `budget_limited_candidate_count_mean=0`.

This diagnostic concentrates on DT-risk / low-margin trials and windows to clarify the risk-response behavior and the efficiency boundary imposed by forced near / heading / history candidates.

## 3. Target Selection Rule

Targets are selected from existing flight20 closed-loop step-level results. A risk step is any step with a DT warning, H2/H3 warning, H1/H2/H3 margin violation, `critical` or `recovery_support` mode, fallback use, or low current/min safety h at or below the DT margin.

Trials are ranked by DT-warning count descending, low-margin count descending, min_safety_h ascending, then H3 violation count descending. The default selects top 5 trials, with previous hotspot trials available as supplements only if too few selected trials contain DT warnings.

Target windows are analysis windows only. The runner starts from each trial start because mid-step closed-loop initialization is not implemented here.

## 4. Compared Profiles

The diagnostic compares fixed V1 and adaptive_balanced. Adaptive conservative is not part of the default diagnostic.

## 5. Recovery Setting

V4-C recovery is disabled to isolate Adaptive V1 candidate budgeting from the optional predictive recovery module.

## 6. Metrics

Metrics include runtime mean/p95/max, selected_K mean/p95/max, selected_K_applied_rate, measured candidate count mean/p95/max, active constraints, collision count, QP infeasible count, min_safety_h_min, H1/H2/H3 margin violation counts, DT/H2/H3 warning counts, low-margin count, mode counts, fallback count/fraction, recovery_used_count, crash_count, progress_mean, and candidate decomposition fields.

## 7. Candidate Dominance Diagnostic

The analysis explicitly checks forced_near_candidate_count, heading_candidate_count, history_candidate_count, forced_unique_candidate_count, final_unique_candidate_count, budget_limited_candidate_count, forced_candidate_fraction, measured candidate count ratio, selected_K ratio, and whether lowering selected_K changes the final candidate count.

## 8. Decision Criteria

If targeted DT-risk closed-loop remains stable but candidate count does not change, Adaptive V1 remains a support module / ablation rather than a main method. If selected_K produces real final candidate count or runtime changes without safety degradation, a broader pilot can be considered. If collision, QP infeasibility, or abnormal runtime appears, Adaptive V1 closed-loop should pause.

This diagnostic does not by itself justify full100.
