# Adaptive V1 Closed-Loop Positioning Update

## Current Positioning

Closed-loop smoke can support the claim that Adaptive V1 balanced is technically integrated into the V1 candidate budgeting / CBF filtering pipeline, if `selected_K_applied_rate=1.0` and recovery remains disabled.

## Safe To Write

- Adaptive V1 balanced was tested in closed-loop smoke.
- The scheduler-selected budget was passed into candidate budgeting.
- Smoke-scale collision, QP, runtime, and DT margin metrics can be reported as smoke results.
- In the smoke cases, measured candidate count was still dominated by forced candidate inclusion, so the smoke validates integration rather than efficiency improvement.

## Still Not Safe To Claim

- Do not claim full benchmark performance.
- Do not claim full100 readiness.
- Do not claim closed-loop runtime improvement beyond the smoke scope.
- Do not claim Adaptive V1 is an independent safety guarantee.

## Method Placement

Adaptive V1 remains an efficiency / risk-response support module. Flight20 closed-loop evidence is needed before promoting it beyond ablation/support-module status.
