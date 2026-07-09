# Next Step After Theoretical Systematization

## 1. Immediate Next Step

Begin integrating the paper's **Introduction**, **System Overview**, and
**Method** sections around the four failure modes and six assurance contracts.
Use the paper-ready insert as source text, but keep every empirical statement
linked to a tracked report and every deployment statement marked as future
work until real-robot evidence exists.

The first paper draft should present one main chain:

> nominal command + baseline CBF-QP -> Start-Safe certification -> H-step DT
> Verification -> optional triggered V4-C recovery.

## 2. Do Not Do Now

- Do not open a new Adaptive branch.
- Do not continue FC-Aware evaluation.
- Do not restart primitive MPC-style recovery.
- Do not run full100 or any new experiment for this systematization task.
- Do not describe real-robot deployment as a completed experiment.
- Do not promote diagnostic branches into the final method.
- Do not claim a new planner, localization method, CBF theorem, four-wheel
  dynamics validation, or global safety guarantee.

## 3. What to Do Before the Paper Draft

- Draw the safety assurance pipeline figure with baseline, proposed, optional,
  diagnostic, and future-deployment components visually separated.
- Draw the four-part failure-mode taxonomy figure.
- Consolidate final result tables without merging margin warnings, QP
  infeasibility, and collision into one outcome.
- Insert and review the claim-boundary table.
- Map every quantitative and qualitative claim to a tracked report.
- Verify that missing scripts or result summaries remain honestly marked in
  `REPRODUCIBILITY_MANIFEST.md`.
- Use `min_safety_h` only as the repository GSplat safety-function value, not
  metric clearance.

## 4. What to Do Before a Real-Robot Experiment

- Confirm the physical command API (`cmd_vel`, Ackermann, or another explicit
  interface) and enforce its limits.
- Confirm the pose source, timestamp behavior, validity signal, and map-frame
  convention.
- Calibrate and validate the GSplat-to-robot/world transform.
- Implement and independently test the emergency-stop and fallback path.
- Replace or validate the DT rollout adapter against the robot command-response
  dynamics and measured latency.
- Validate synchronized logging for nominal, filtered, and executed commands,
  safety values, warnings, recovery, solver status, and stop events.
- Start with shadow mode and stop-only mode before low-speed bounded recovery.
- Run only staged low-speed scenes with a safety operator and hardware
  emergency stop.

## 5. Pre-Draft Adversarial Self-Review

| Dimension | Current assessment | Required paper action |
| --- | --- | --- |
| Contribution | Pass for systematization, but not as a new CBF theorem | Present the failure-mode taxonomy, assurance contracts, and bounded module composition as the organizing contribution; do not inflate individual wrappers |
| Writing clarity | Pass at the framework level | Keep the terms Start-Safe, DT Verification, V4-C, margin warning, collision, and repository `h` consistent across Introduction and Method |
| Experimental strength | Mixed and configuration-dependent | Link every empirical statement to its exact report/configuration; retain negative flight and diagnostic evidence rather than generalizing from selected successful runs |
| Evaluation completeness | Sufficient for organizing existing evidence, incomplete for real-world claims | Do not claim completed real-robot validation or universal cross-scene superiority; preserve manifest gaps and future deployment requirements |
| Method design soundness | Conditional on declared safety query, rollout model, limits, and interfaces | State assumptions beside each contract and treat model mismatch, stale pose, failed recovery, and adapter failure as explicit failure conditions |

Major claim-evidence map:

- **Claim:** the framework covers four deployment failure modes.
  **Evidence:** the taxonomy and one-to-one module mapping.
  **Status:** supported as a systematization contribution.
- **Claim:** Start-Safe certifies or repairs an initial state.
  **Evidence:** tracked StartGuard, V4-A, and synthetic initial-unsafe reports.
  **Status:** supported within repository `h` and full-query validation scope.
- **Claim:** collision-free execution can contain DT margin warnings.
  **Evidence:** the tracked DT Verification consolidation.
  **Status:** supported for the audited simulation trajectories.
- **Claim:** triggered V4-C reduces executed horizon-margin violations.
  **Evidence:** tracked V4-C recovery reports.
  **Status:** supported only for the named tested configurations.
- **Claim:** the method is validated on a real four-wheel robot.
  **Evidence:** no completed deployment evidence in the current repository.
  **Status:** unsupported; retain as interface contract and future experiment.
