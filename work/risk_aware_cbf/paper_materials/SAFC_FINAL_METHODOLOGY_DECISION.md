# SAFC Final Methodology Decision

## 1. Formal Method Name

The current complete methodology should be named:

**Certified Feasibility-Aware Start-Safe CBF with H-Step Discrete-Time
Verification, Optional Triggered Predictive Recovery, and Safety-Assurance
Feedback Coordination.**

## 2. Main Method Identity

The main method remains:

```text
Certified Feasibility-Aware Start-Safe CBF
+ H-Step Discrete-Time Verification
+ Optional Triggered Predictive Recovery
+ Safety-Assurance Feedback Coordinator
```

This identity is more rigorous than presenting SAFC as a standalone planner or
as a general performance-improvement module.

## 3. Final Role of Warning-Streak Slowdown

Final role: **optional bounded feedback action / diagnostic extension**.

It should not be labeled as the core contribution. The evidence supports
natural warning-gated activation, fixed-case A/B behavior, small-cohort
targeted behavior, and robustness diagnosis. It does not support generalized
warning reduction, completion improvement, or planner-quality claims.

## 4. SAFC Module Status

SAFC has moved from a text-only architecture to a method module with bounded
validation support. The evidence includes:

- Level 1 offline reconstruction;
- Level 2 no-op instrumentation;
- Level 3A warning-streak slowdown smoke;
- Level 3B / 3B-R warning-rich context discovery and reconciliation;
- Level 3B-Active fixed C003 activation;
- Level 3C fixed C003 A/B;
- Level 3D small targeted cohort;
- Level 3E robustness and failure diagnosis;
- VANS shadow-only counterfactual feasibility audit as a diagnostic extension.

## 5. Evidence Supporting the Decision

- Level 3D produced a total warning delta of -25, with 3/5 lower, 1/5 equal,
  and 1/5 higher warning counts.
- Level 3E current_policy total warning steps were 164.
- Level 3E milder_slowdown and critical_only_slowdown totals were both 182.
- C004 remains negative and scale-sensitive.
- C006 remains neutral.
- All Level 3E completion counts were 0.
- Control scope remained wrapper-level in the tested active paths.
- VANS shadow audit completed five pre-registered contexts with state
  isolation passed; it found one verified alternative step in C002, zero
  progress-nonworse verified alternative steps, and no verified alternatives
  for C004 or C006.

## 6. Need for Level 3F

Level 3F is not required before paper-outline preparation. It would only be
needed if the target claim changes to planner integration, benchmark
performance, or real-robot deployment.

## 7. Stop Adding Method Modules

New method modules should stop for now. Additional modules would make the
method story less rigorous unless tied to a single clearly blocking gap.
Verification-Aware Nominal Action Selection is not promoted to the core method
by the shadow audit; its decision is `retain_as_diagnostic_extension`.

## 8. Paper Outline Readiness

The project can proceed to paper outline / method-storyline organization. The
outline must preserve the distinction between core supported method,
configuration-limited recovery evidence, targeted SAFC observations,
interface-level contracts, and future work.

## 9. Claims That Must Remain Limited

- SAFC active feedback is not benchmark-validated.
- Warning-streak slowdown does not generally reduce warnings.
- Collision count comparisons do not prove generalized collision reduction.
- Progress proxy is not completion or planner quality.
- VANS shadow evidence is not active VANS validation and does not establish
  warning reduction, completion improvement, or planner-quality improvement.
- Real-robot deployment is not validated.
- Planner integration is not complete.
- No new CBF theorem is established.

## 10. Future Work Not to Implement in the Current Paper

- full100 expansion solely for SAFC active slowdown;
- planner integration;
- risk-cost planner optimization;
- waypoint screening implementation;
- real-robot claims;
- new recovery branches;
- active Verification-Aware Nominal Action Selection;
- unsupported performance claims.
