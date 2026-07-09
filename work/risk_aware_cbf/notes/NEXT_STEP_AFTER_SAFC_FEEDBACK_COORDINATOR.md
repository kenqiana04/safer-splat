# Next Step After SAFC Feedback Coordinator

## 1. What SAFC Adds

SAFC converts the prior linear Start-Safe--CBF-QP--DT
Verification--Triggered Recovery chain into a feedback-augmented assurance
architecture. It assigns safety signals to a supervisory state, bounded action,
feedback contract, implementation status, and non-claim. This provides a
closed-loop paper narrative without claiming a new planner or theorem.

## 2. Current Status

SAFC is currently theory, architecture, and paper-organization material. It is
not yet a new end-to-end experimental module. The only feedback connection
already supported by tracked experiments is the named
verification-to-triggered-V4-C path. Command shaping, replanning, planner
risk-cost updates, waypoint screening, the full S0--S6 supervisor, and
real-robot halt integration remain interface-level or future work.

## 3. What Not to Do Now

- Do not immediately implement a global planner.
- Do not immediately implement a complex local planner.
- Do not continue FC-Aware.
- Do not restart Adaptive.
- Do not restart primitive MPC-style recovery.
- Do not claim improved path-planning accuracy or planner optimality.
- Do not claim completed real-robot or four-wheel validation.
- Do not run full100, flight20 continuation, or new V4-C experiments as part of
  this documentation task.

## 4. If We Later Want Experiments

### Experiment Candidate A: Verification-Aware Nominal Action Selection

Expose a small fixed candidate set from an existing nominal source and compare
H-step risk scores before ordinary CBF-QP filtering. Start with a smoke test,
then a targeted warning-window audit; claims must remain about candidate
selection under the tested source, not a new planner.

### Experiment Candidate B: Warning-Streak Slowdown Policy

Implement a bounded slowdown factor driven by `warning_streak` and released
only after `clear_streak >= K_exit`. Separate smoke, targeted risk-window, and
collision/margin reporting, and do not claim planner improvement.

### Experiment Candidate C: Replan-Request Logging Only

Generate `replan_request` events and reason codes without executing a planner,
then audit trigger precision against persistent warning, recovery, and progress
signals. This would validate the interface logic only, not replanning success.

### Experiment Candidate D: Waypoint Screening Offline Audit

Screen a fixed, externally generated waypoint set with repository `h` and
optional H-step checks. Report rejection/acceptance behavior and false
assumptions explicitly; do not infer global path safety or planner completeness.

Each candidate requires a separate specification, smoke test, targeted
evaluation, stopping rule, and claim-boundary review before implementation.
None is run in the current task.

## 5. Immediate Paper Writing Step

Begin integrating:

- Introduction;
- System Overview;
- Method;
- Figure 1 feedback-augmented pipeline;
- failure-mode table;
- SAFC feedback-contract table; and
- claim-boundary table.

The first integrated draft should use one consistent story:

> failure mode -> assurance signal -> SAFC state -> bounded feedback contract
> -> verified execution, external interface, or conservative halt.

## 6. Pre-Draft Adversarial Self-Review

| Dimension | Assessment | Required action |
| --- | --- | --- |
| Contribution | SAFC adds a coherent feedback architecture, but not new empirical performance | Present signal/state/contract integration as the contribution; do not imply implemented planner feedback |
| Writing clarity | Terminology and status levels are explicit | Keep `implemented / supported`, `interface-level`, and `future extension` consistent throughout the paper |
| Experimental strength | No new SAFC experiment exists | Restrict empirical statements to tracked Start-Safe, DT, and V4-C reports |
| Evaluation completeness | Sufficient for architecture documentation, incomplete for planner/robot claims | Keep future experiments and deployment validation visibly separate |
| Method design soundness | Fail-safe semantics are defined, but thresholds/adapters require later validation | Treat `K_enter`, `K_exit`, risk-cost mapping, command shaping, and physical stop behavior as configuration/interface assumptions |

Major claim-evidence map:

- **Claim:** SAFC converts assurance signals into a contract-based feedback
  architecture. **Evidence:** the coordinator, state-machine, feedback-contract,
  planner-interface, and pipeline documents. **Status:** supported as a
  theoretical/architectural contribution.
- **Claim:** verification-triggered recovery has current empirical support.
  **Evidence:** tracked V4-C reports. **Status:** supported only for named
  configurations.
- **Claim:** planner-facing feedback improves planning. **Evidence:** no current
  integration experiment. **Status:** unsupported; retain as interface/future.
- **Claim:** the S0--S6 supervisor is end-to-end implemented. **Evidence:** no
  current implementation. **Status:** unsupported; describe as specification.
- **Claim:** physical halt and four-wheel deployment are validated.
  **Evidence:** interface contract only. **Status:** unsupported; retain as
  future deployment work.
