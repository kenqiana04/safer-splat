# Paper Framework Repositioning

## 1. Recommended Problem Definition

Recommended English framing:

```text
Given an existing GSplat-based navigation pipeline and a nominal controller, we study how to provide a feasibility-aware and discrete-time verified safety assurance layer that detects unsafe starts, filters nominal commands, verifies short-horizon sampled-data risks, and triggers recovery when needed.
```

This makes the contribution a safety assurance layer, not a planner, localization system, or full robot autonomy stack.

## 2. Recommended Title Options

1. Feasibility-Aware and Discrete-Time Verified Safety Assurance for GSplat-Based Robot Navigation
2. A Deployable Safety Assurance Layer for Gaussian-Splatting-Based Mobile Robot Navigation
3. Start-Safe and Discrete-Time Verified CBF Filtering for GSplat Navigation
4. Towards Deployable Safety Assurance for Mobile Robot Navigation in Gaussian Splatting Maps
5. Feasibility-Aware CBF Safety Filtering with Discrete-Time Verification in GSplat Maps

Do not include "four-wheel" in the title unless a four-wheel-specific dynamics and command adapter are implemented and evaluated.

## 3. Contributions

Recommended contribution wording:

1. Start-state feasibility certification and repair for GSplat safety filtering.
2. Discrete-time H-step verification for sampled-data safety risk.
3. Triggered predictive recovery under DT warning conditions.
4. System-level simulation evidence and real-robot deployment plan.
5. Diagnostic analysis of efficiency and recovery branches, including frozen negative results.

Do not list planner design, localization, mapping, or four-wheel robot dynamics as contributions.

## 4. Paper Structure

Suggested structure:

1. Introduction
2. Related Work
3. System Overview
4. Feasibility-Aware Safety Assurance Layer
5. Discrete-Time Verification and Triggered Recovery
6. Simulation Experiments
7. Real-Robot Deployment Plan
8. Diagnostic Ablations and Negative Results
9. Limitations
10. Conclusion

## 5. How to Describe SAFER Baseline

SAFER should be treated as a GSplat-based safety-filtering baseline / environment. It provides the GSplat safety map query, CBF-QP action filtering path, double-integrator simulation interface, and closed-loop benchmark context.

Our method extends this safety-filtering perspective with start feasibility, start repair, H-step DT verification, and triggered recovery. It does not replace SAFER's core map query or claim to be a new nominal planner.

## 6. How to Avoid Overclaiming

| Forbidden phrase | Safer alternative |
|---|---|
| We propose a new planner. | We propose a planner-agnostic safety assurance layer. |
| We solve four-wheel robot navigation. | We outline a deployment path for mobile robot experiments. |
| We guarantee safety. | We verify short-horizon sampled-data risks and report collision outcomes separately. |
| We improve localization. | We assume a pose source and require frame alignment for deployment. |
| Our method passes a full real-world benchmark. | We plan minimal real-robot deployment demonstrations. |
| FC-Aware improves runtime. | FC-Aware is a diagnostic / targeted ablation and is frozen as a main branch. |
| Adaptive V1 improves efficiency. | Adaptive V1 showed risk-response behavior but not reliable candidate-count/runtime improvement. |
| MPC-style recovery outperforms V4-C. | MPC-style recovery is a negative diagnostic / future-work branch. |

## 7. Recommended Main Claim

```text
The paper studies how to make GSplat-based CBF navigation safer to initialize and safer to execute in sampled time by adding start-state feasibility checks, repair, H-step verification, and triggered recovery around an existing nominal command source.
```

## 8. Explicit Limitations to Include

- The current simulation dynamics are a 3D double integrator, not a four-wheel model.
- `h` and `min_safety_h` are safety-function values, not meter clearance.
- Margin violation is not collision.
- The current repository does not implement a full global planner.
- The current repository does not implement localization or robot command interfaces.
- Frozen branches should be reported as diagnostics, not as final methods.
