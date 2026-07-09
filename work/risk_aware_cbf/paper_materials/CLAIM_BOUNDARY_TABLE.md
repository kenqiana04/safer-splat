# Claim Boundary Table

This table prevents unsupported claims and links each permitted statement to
its actual evidence scope. A "Yes" means the statement is supportable only
with the boundary shown; it does not expand the evidence into a theorem or a
different experimental domain.

| Claim candidate | Can claim? | Evidence | Boundary / safer wording |
| --- | --- | --- | --- |
| We propose a new global planner. | No | Repository navigation-stack audit found no explicit global planner. | We assume an external or baseline nominal command source. |
| We propose a new local planner. | No | Repository audit identifies a simple goal-directed nominal controller, not an obstacle-aware local planner. | The safety layer filters a nominal command supplied by the baseline or an external navigation stack. |
| We propose a new localization method. | No | No localization interface or localization algorithm is implemented in the audited repository. | We assume a pose source and require map-frame alignment for deployment. |
| We validate four-wheel robot dynamics. | Not yet | The current simulation uses a 3D double-integrator point model. | We provide a real-robot adapter contract and deployment plan; four-wheel validation requires a matching adapter, model, and experiments. |
| We provide a global safety guarantee. | No | Available evidence is repository-scoped certification, finite-horizon verification, and empirical collision reporting. | We provide module-level assurance under stated assumptions and report collision outcomes separately. |
| We provide a new CBF theorem. | No | The work uses the existing CBF-QP filtering path and wrapper-side assurance modules. | We systematize start feasibility, finite-horizon verification, and triggered recovery without claiming a new CBF theorem. |
| We provide start-state feasibility certification / repair. | Yes | StartGuard and synthetic initial-unsafe stress reports; full-query validation is reported under repository `h`. | Certification is limited to the repository safety field, selected thresholds, repair domain, and validation queries. |
| We show collision-free baseline full100. | Only for a precisely named supported configuration | The original flight SAFER-Splat baseline in `REPORT_RISK_AWARE_V1_FLIGHT_100_TRIAL.md` reports one collision. The Start-Safe/post-repair V4-A configuration in `REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md` reports 100/100 collision-free trials. | Do not call the post-repair or recovery-enabled result the unqualified original baseline. State the exact configuration and tracked report; empirical collision-free performance is not a global guarantee. |
| We show collision-free does not imply sampled-data margin safety. | Yes | `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md` reports collision-free execution with nonzero H-step margin violations in the verification-only audit. | A DT margin violation is a finite-horizon warning, not collision. |
| We show triggered recovery can remove executed H-step margin violations in tested V4-C settings. | Yes | `REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md` and `REPORT_V4C_FLIGHT100_VALIDATION.md`. | Restrict the claim to the tested scenes, horizons, margin, dynamics, candidate set, and report configuration. |
| Adaptive V1 improves efficiency. | No | Adaptive studies are diagnostic and do not establish a final, broadly supported efficiency claim. | Adaptive V1 is an ablation / diagnostic branch and is not part of the final main method. |
| FC-Aware V1 is the final method. | No | The reconciliation report freezes FC-Aware V1 as diagnostic/ablation evidence. | FC-Aware V1 is not the final method and does not replace Start-Safe, DT Verification, CBF-QP, or optional recovery. |
| FC-Aware V1 caused collision. | No | Both fixed and capped configurations encountered collision in the reconciled trial; attribution to the cap is unsupported. | The recovery-disabled evaluation exposed an unsafe condition in both compared configurations; causality is not assigned to FC-Aware V1. |
| Primitive MPC-style recovery is successful. | No | The branch is retained as a negative diagnostic / future-work direction. | Do not promote the primitive MPC-style branch to a validated recovery method. |
| The real-robot experiment proves full benchmark superiority. | No | Real-robot implementation and validation are not complete in this repository. | The current materials define a deployment interface and minimal future experiments, not completed real-world superiority. |
| The proposed framework is planner-agnostic. | Yes | Contracts consume `u_nom` at a command boundary and do not require a particular planner implementation. | Planner-agnostic means compatible at the declared nominal-command interface; it does not imply compatibility with every robot without an adapter. |
| `min_safety_h` is metric obstacle clearance. | No | Repository reports define it as a GSplat ellipsoid safety-function value. | Report `min_safety_h` as the repository safety value; use a separate validated evaluator for metric clearance. |
| A DT margin violation is a collision. | No | DT consolidation explicitly separates finite-horizon margin warnings from collision checks. | Report warning/margin metrics and collision metrics in separate fields. |
| V4-C replaces the nominal controller or CBF-QP. | No | Source audit and V4-C reports describe optional triggered wrapper-side recovery. | V4-C is activated by predicted risk, evaluates candidates, executes the selected first action, and retains the nominal and CBF-QP interfaces. |
