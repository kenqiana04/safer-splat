# SAFC Final Method-Validation Package

## 1. Purpose

This package consolidates the completed SAFC methodology and its validation
evidence. It is not a paper draft and does not introduce new experimental
claims.

The package freezes the method-validation boundary after Level 1 through Level
3E. It should be used to prepare a later paper outline, system figure, and
claim table without adding new method branches by default.

## 2. Final Methodology Architecture

The final methodology is a certification and supervision stack, not a new
global planner:

1. Nominal command contract: an external or baseline command source supplies
   `u_nom`.
2. Start-Safe feasibility certification: start states are admitted, repaired,
   or rejected under the repository safety field.
3. CBF-QP safety filtering: the existing safety filter maps `u_nom` to the
   filtered command under the implemented CBF-QP path.
4. H-step discrete-time verification: finite-horizon margin checks diagnose
   sampled-data risk after filtering.
5. Triggered predictive recovery: named V4-C configurations may be activated
   by predicted finite-horizon risk.
6. SAFC supervisory state machine: assurance events are mapped to explicit
   states and bounded feedback candidates.
7. Bounded feedback actions: warning-gated command shaping is implemented as a
   wrapper-level targeted action; other feedback actions remain interface-level
   unless separately validated.
8. Planner/deployment interfaces: replan requests, risk-cost feedback,
   waypoint screening, and deployment halt are contracts, not completed
   planner or robot validation.
9. Safe-halt boundary: invalid deployment interfaces or unrecoverable safety
   failures must not be described as safe execution.

## 3. Failure Modes

| Failure mode | Method component | Evidence |
| --- | --- | --- |
| F1 Start-State Unsafety | Start-Safe certification and repair | StartGuard, synthetic initial-unsafe stress, repair ablations, and post-repair navigation reports |
| F2 CBF-QP Feasibility Failure | CBF-QP status logging and feasibility-aware admission | baseline audits, Start-Safe feasibility review, Level-1 reconstruction |
| F3 Sampled-Data Margin Risk | H-step discrete-time verification and warning signals | DT verification consolidation, V4-B/V4-C reports, SAFC Level 1 through Level 3E |
| F4 Recovery Insufficiency | Triggered V4-C recovery and escalation contracts | V4-C runtime/flight validation reports and SAFC feedback contracts |

These failure modes are method-design anchors. They do not prove global safety
or planner optimality.

## 4. Assurance Contracts

| Contract | Role | SAFC relation |
| --- | --- | --- |
| C0 Nominal Command Contract | Defines the `u_nom` boundary and prevents claiming a new planner | SAFC may shape wrapper-level execution only under declared gates |
| C1 Start-Safe Feasibility Certification | Certifies, repairs, or rejects start states | SAFC consumes start admissibility signals |
| C2 CBF-QP Safety Filtering | Performs instantaneous safety filtering | SAFC observes status and does not modify the CBF-QP |
| C3 H-Step Discrete-Time Verification | Checks finite-horizon sampled-data margin risk | SAFC uses warnings as event inputs |
| C4 Triggered Predictive Recovery | Provides named optional recovery configurations | SAFC may trigger recovery under contract |
| C5 Real-Robot Deployment Adapter | Defines pose, frame, command, speed, and stop assumptions | SAFC treats invalid deployment interfaces as halt/not-certified conditions |
| FBC-1 Verification-to-Command-Shaping | Converts warning evidence into bounded slowdown | Implemented only as targeted wrapper-level warning-streak slowdown |
| FBC-2 Verification-to-Recovery | Converts persistent H-step risk into recovery activation | Supported for named V4-C settings |
| FBC-3 Recovery-to-Replan | Escalates repeated local safety symptoms | Interface-level only |
| FBC-4 Safety-to-Risk-Cost | Exposes risk feedback to a future planner | Future work only |
| FBC-5 Start/Goal-to-Waypoint-Screening | Rejects unsafe candidate states | Future interface only |
| FBC-6 Deployment-to-Halt | Defines conservative stop/abort semantics | Deployment contract, not robot validation |

## 5. SAFC Validation Ladder

| Level | Objective | Evidence | Validated statement | Non-validated statement | Report path | Result path |
| --- | --- | --- | --- | --- | --- | --- |
| Level 1 | Offline event reconstruction | existing reports mapped to SAFC states | prior safety events can be reconstructed into SAFC states/actions | no new closed-loop behavior | `work/risk_aware_cbf/REPORT_SAFC_LEVEL1_OFFLINE_RECONSTRUCTION.md` | `work/risk_aware_cbf/results/safc_level1_offline_reconstruction/` |
| Level 2 | No-op closed-loop instrumentation | tiny closed-loop no-op instrumentation | SAFC can be inserted passively without command modification | active feedback effectiveness | `work/risk_aware_cbf/REPORT_SAFC_LEVEL2_NOOP_INSTRUMENTATION.md` | `work/risk_aware_cbf/results/safc_level2_noop_instrumentation/` |
| Level 3A | Policy logic and integration | warning-streak slowdown smoke | bounded slowdown logic and integration are executable | benchmark improvement | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3A_WARNING_SLOWDOWN.md` | `work/risk_aware_cbf/results/safc_level3a_warning_slowdown/` |
| Level 3B | Warning-rich discovery | targeted discovery attempt | discovery process and failure modes are recorded | full warning-rich benchmark coverage | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3B_WARNING_RICH_TARGETED.md` | `work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted/` |
| Level 3B-R | Warning-context reconciliation | report-derived and executable contexts compared | warning evidence must be reproduced before active claims | synthetic warning injection as natural evidence | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3BR_WARNING_RECONCILIATION.md` | `work/risk_aware_cbf/results/safc_level3br_warning_reconciliation/` |
| Level 3B-Active | Fixed-candidate activation | C003 active slowdown | natural warning-gated activation and wrapper scope are validated on fixed C003 | performance improvement | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3B_ACTIVE_C003_SLOWDOWN.md` | `work/risk_aware_cbf/results/safc_level3b_active_c003_slowdown/` |
| Level 3C | Fixed-C003 targeted A/B | C003 no-op vs active | fixed-case A/B behavior and control scope are recorded | generalized warning reduction | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3C_FIXED_C003_AB.md` | `work/risk_aware_cbf/results/safc_level3c_fixed_c003_ab/` |
| Level 3D | Small targeted cohort | five pre-registered candidates | active slowdown produced fewer warnings in 3/5, equal in 1/5, more in 1/5 | benchmark-level claim | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3D_SMALL_TARGETED_COHORT.md` | `work/risk_aware_cbf/results/safc_level3d_small_targeted_cohort/` |
| Level 3E | Robustness and failure diagnosis | three policy variants over five candidates | mixed outcomes, C004, C006, stop reasons, and scope boundaries are diagnosed | generalized performance improvement | `work/risk_aware_cbf/REPORT_SAFC_LEVEL3E_ROBUSTNESS_DIAGNOSIS.md` | `work/risk_aware_cbf/results/safc_level3e_robustness_diagnosis/` |
| VANS Shadow | Verification-aware nominal-action selection feasibility audit | shadow-only counterfactual evaluation over five pre-registered contexts | one verified alternative nominal action was found without executing it; state isolation passed | active VANS effectiveness, warning reduction, completion improvement, planner improvement | `work/risk_aware_cbf/REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md` | `work/risk_aware_cbf/results/vans_shadow_feasibility_audit/` |

## 6. Final Evidence Summary

- Level 3D: active warning fewer in 3/5, equal in 1/5, more in 1/5.
- Level 3D total warning delta: -25.
- Level 3E current total: 164.
- Level 3E milder total: 182.
- Level 3E critical-only total: 182.
- C004 is negative and scale-sensitive.
- C006 is neutral.
- All Level 3E completion counts are 0.
- VANS shadow audit found 1 verified alternative step in C002, 0
  progress-nonworse verified alternative steps, and no C004/C006 verified
  alternative steps.
- No generalized performance claim is supported.

## 7. Final Method Classification

### Core supported method

- Start-Safe certification/repair.
- CBF-QP filtering.
- H-step discrete-time verification.
- Triggered V4-C recovery in named configurations.
- SAFC state/event coordination.
- No-op instrumentation.
- Warning-gated wrapper-level command shaping mechanism.

### Bounded targeted evidence

- warning-streak slowdown activation;
- fixed-candidate A/B;
- small targeted cohort behavior;
- policy-variant robustness diagnosis.
- VANS shadow-only counterfactual feasibility audit as a diagnostic extension.

### Interface-level only

- replan request;
- planner risk-cost update;
- waypoint screening;
- deployment halt adapter.

### Future work

- planner integration;
- real robot;
- navigation-stack validation;
- general performance benchmark;
- statistical evaluation.
- active Verification-Aware Nominal Action Selection.

## 8. Final Claim Boundary

The final package supports method-architecture and bounded validation claims.
It does not support generalized warning reduction, generalized collision
reduction, planning accuracy improvement, planner optimality, complete
real-robot validation, global safety, or a new CBF theorem.

## 9. Remaining Limitations

- All active diagnostic cases did not reach goal.
- The warning-rich evidence is limited to a small targeted cohort.
- Active command scaling changes subsequent trajectories, so comparisons are
  targeted behavioral observations rather than same-trajectory causal proof.
- No statistical significance is established.
- Some original report contexts were not reproducible without reconciliation.
- No real-robot validation is complete.
- No planner integration is complete.
- Verification-Aware Nominal Action Selection has not been actively
  validated; shadow counterfactual opportunities are not closed-loop results.

## 10. Final Decision

1. SAFC methodology design is conditionally complete as a supervisory
   assurance module, not as a planner or robot deployment stack.
2. The validation chain is complete enough for method-storyline preparation
   because Level 1 through Level 3E cover reconstruction, instrumentation,
   activation, targeted A/B, cohort behavior, and robustness diagnosis.
3. Active warning-streak slowdown should be presented as an optional bounded
   feedback action and diagnostic extension, not the core contribution.
4. SAFC has moved from a text-only architecture to a method module with
   bounded validation support.
5. The supporting evidence is the Level 1 through Level 3E report chain plus
   the contract and state-machine documents.
6. Level 3F is not required before paper-outline preparation unless the paper
   aims to claim planner integration or benchmark performance.
7. New method modules should stop for now.
8. The next step should be paper outline and method-storyline organization.
9. Claims must remain bounded to named configurations and targeted evidence.
10. Planner integration, real-robot claims, statistical benchmarking, and new
    recovery branches should remain future work.
11. Verification-Aware Nominal Action Selection should remain a diagnostic
    extension unless a separate bounded active prototype is validated.
