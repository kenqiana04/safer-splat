# Adaptive V1 Experiment Narrative

## 1. Why Adaptive V1 Was Tested

Fixed V1 candidate budgeting cannot respond to DT-warning or low-margin states. Adaptive V1 was tested to see whether the candidate budget could increase around risky sampled-data states and potentially reduce dense CBF construction cost in safer states.

## 2. What The Experiment Found

The risk response worked:

- `selected_K` was applied to the V1 selector in closed-loop pilots.
- `selected_K` increased in DT-risk and low-margin windows.
- Closed-loop pilot safety metrics did not degrade relative to fixed V1.
- V4-C recovery was disabled, and recovery was not used.

The efficiency claim did not hold:

- measured final candidate count did not materially change,
- targeted risk-window measured candidate-count ratio balanced/fixed was `0.999773`,
- no runtime improvement claim is supported.

## 3. Why Efficiency Gain Did Not Appear

The V1 selector first unions forced near, heading, and history candidates. Heading candidates dominate this forced union. Since the forced union already exceeds the selected budget, the optional risk-ranked fill receives zero budget. The final union has no post-cap, so final candidate count remains large even when `selected_K` changes.

## 4. How To Report It

Report Adaptive V1 as an ablation / diagnostic:

- useful evidence that risk-responsive scheduling is integrated,
- useful systems insight into why candidate-count reduction fails,
- not a main method,
- not a runtime-improvement result.

## 5. Effect On Paper Main Line

This does not weaken the FAS-CBF main line. The main contributions remain:

1. Certified Feasibility-Aware Start-Safe CBF,
2. Discrete-Time Verification,
3. optional triggered Predictive Recovery.

Adaptive V1 remains a support module and ablation. Optional recovery remains separately positioned as a triggered module, not an always-on default controller.

