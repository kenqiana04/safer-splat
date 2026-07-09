# Theoretical Systematization Overview

## 1. Motivation

Existing GSplat-based control barrier function (CBF) safety filters are effective
as instantaneous action filters, but deployment-oriented navigation safety
requires more than solving a per-step CBF-QP. A deployable safety layer must
also reason about whether the initial state is admissible, whether the CBF-QP
remains feasible under the selected model and bounds, whether sampled-data
execution creates short-horizon margin risks, and whether a detected risk can
be converted into an executable recovery action.

We therefore frame the contribution as a **planner-agnostic safety assurance
layer for GSplat-based robot navigation**. The framework does not introduce a
global planner, local planner, localization method, or four-wheel-specific
dynamics model. It accepts a nominal command from an external source or the
baseline goal-directed controller and augments the existing GSplat CBF
filtering path with explicit start-state certification, discrete-time
verification, and optional risk-triggered recovery.

The resulting main line is:

> Certified Feasibility-Aware Start-Safe CBF + H-step Discrete-Time
> Verification + optional triggered V4-C Predictive Recovery.

## 2. Core Systematization

### F1. Start-State Unsafety

The robot starts inside or too close to the unsafe set, so downstream filtering
begins from an invalid or low-margin condition. A controller that assumes an
admissible start cannot repair this assumption merely by continuing normal
closed-loop execution.

### F2. CBF-QP Feasibility Failure

The instantaneous CBF-QP may become infeasible or unreliable when the initial
or current state does not admit a safe corrective action under the selected
constraints, dynamics model, and control bounds. Solver infeasibility is a
control-feasibility outcome and must be reported separately from geometric
collision.

### F3. Sampled-Data Margin Risk

Even when the instantaneous filtered action is feasible, its sampled-data
rollout over future steps may approach a low-margin region. A pointwise
filtering result therefore does not, by itself, establish an H-step margin
property.

### F4. Recovery Insufficiency

Detecting a predicted short-horizon risk is insufficient unless the system has
a response mechanism that can select an executable safer action. Recovery is
needed only when verification raises a warning; it need not replace the
nominal controller during normal operation.

## 3. Mapping to Proposed Modules

| Failure mode | Baseline limitation | Proposed response | Evidence source |
| --- | --- | --- | --- |
| F1 Start-State Unsafety | Baseline execution assumes a valid start. | Start-Safe Feasibility Certification / Repair | `REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md`; StartGuard reports tracked in the repository |
| F2 CBF-QP Feasibility Failure | An instantaneous QP can fail or become unreliable under an inadmissible state or selected bounds. | Feasibility-aware certification, repair, and full-query validation | `REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md`; compact underlying artifacts remain subject to the release manifest |
| F3 Sampled-Data Margin Risk | Instantaneous CBF-QP feasibility does not imply H-step margin safety. | H-step Discrete-Time Verification | `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md` |
| F4 Recovery Insufficiency | Detection alone does not modify the executed action. | Optional triggered V4-C Predictive Recovery | `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md` and `REPORT_V4C_FLIGHT100_VALIDATION.md` |

The evidence sources above are empirical reports, not substitutes for a global
formal proof. Where the release manifest marks a referenced script or compact
result artifact as absent, that release gap remains explicit.

## 4. Contribution Reframing

1. We introduce a failure-mode taxonomy for deployment-oriented GSplat CBF
   navigation safety.
2. We formulate a modular assurance layer that covers start feasibility,
   sampled-data verification, and triggered recovery.
3. We define assurance contracts for each module, explicitly separating
   certification, verification, recovery, and empirical validation.
4. We provide claim boundaries that prevent overclaiming planner,
   localization, four-wheel dynamics, or global safety guarantees.

## 5. How This Strengthens the Paper

This systematization converts the method from a collection of wrappers into a
structured safety assurance framework. Each module is tied to a specific
deployment failure mode and a bounded assurance contract. This organization
clarifies what is checked before execution, what is filtered instantaneously,
what is verified over a finite horizon, and what action is taken when a warning
is raised.

The framework also separates four levels of evidence: module-level
certification under the repository safety field, short-horizon verification
under the selected simulation dynamics, empirical recovery performance in
tracked experiments, and future real-robot deployment validation. This
separation makes the paper's claims more precise: diagnostic branches remain
ablations, collision outcomes remain distinct from margin warnings, and the
real-robot adapter remains a deployment contract until it is implemented and
tested.
