# Adaptive V1 Flight20 Positioning Update

## Current Positioning

Adaptive V1 balanced remains a candidate budgeting / efficiency / risk-response support module. The flight20 closed-loop pilot can support integration and ablation claims when `selected_K_applied_rate=1.0`, recovery remains disabled, and crash / collision / QP metrics do not degrade.

## Safe To Write

- Adaptive V1 balanced was tested in a flight20 closed-loop pilot.
- The scheduler-selected budget was passed into V1 candidate budgeting.
- Collision, QP, runtime, selected_K, measured candidate count, DT margin, mode-switching, and decomposition metrics can be reported as pilot results.
- V4-C recovery was disabled.

## Still Not Safe To Claim

- Do not claim full100 benchmark performance.
- Do not claim Adaptive V1 is a new CBF theorem.
- Do not claim Adaptive V1 is an independent safety guarantee.
- Do not claim final candidate count or runtime improvement unless the measured flight20 metrics show it.

## Method Placement

Current paper role: `support_module_or_ablation_not_main_safety_method`.

Recommended next experiment: targeted DT-risk closed-loop pilot = `True`.

Full100 now: `False`.
