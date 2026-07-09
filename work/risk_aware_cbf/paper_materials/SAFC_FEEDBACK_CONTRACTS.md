# SAFC Feedback Contracts

## 1. Contract Philosophy

SAFC defines feedback-level contracts. Each contract converts a specific safety
signal into a bounded action and explicitly states what is not claimed. The
contracts specify interfaces and escalation semantics; they do not imply that
all actions are currently implemented, nor do they compose automatically into
a global safety theorem.

Status labels have the following meanings:

- **implemented / supported:** behavior is supported by the current
  reproduction-side implementation and tracked reports for named settings;
- **interface-level:** the signal and contract are specified, but no
  end-to-end planner or deployment implementation is claimed;
- **future extension:** separate implementation, smoke testing, targeted
  evaluation, and claim review are required.

## 2. FBC-1: Verification-to-Command-Shaping Contract

- **Input signals:** H1/H2/H3 minimum `h`, warning flags, `warning_streak`,
  `current_h_min`, `u_nom`, robot/command limits.
- **Trigger:** DT warning, low H-step minimum `h`, low current margin, or a
  persistent warning below the configured policy threshold.
- **Output action:** bounded slowdown factor, scaled nominal command, or
  conservative nominal command bound before ordinary filtering/execution.
- **Assumptions:** command scaling is compatible with the nominal-command and
  CBF-QP interfaces; limits, units, and timing are valid.
- **Assurance scope:** defines a conservative command-shaping response to a
  finite-horizon warning.
- **Non-claims:** does not claim path optimality, planner improvement, global
  safety, or current experimental support.
- **Current status:** interface-level / future extension.

## 3. FBC-2: Verification-to-Recovery Contract

- **Input signals:** H2/H3 warning, H-step minimum `h`, warning streak,
  recovery availability, and baseline filtered command.
- **Trigger:** persistent H-step warning or margin below the configured
  recovery threshold.
- **Output action:** activate optional V4-C Recovery and require
  post-recovery verification.
- **Assumptions:** the named V4-C candidate set, rollout model, limits, and
  activation policy are available and match the evaluated setting.
- **Assurance scope:** connects finite-horizon warning to triggered recovery in
  the tested V4-C configurations.
- **Non-claims:** not always-on MPC, not globally optimal recovery, not a
  replacement for the nominal controller or CBF-QP, and not global safety.
- **Current status:** implemented / supported by tracked V4-C reports for their
  named settings.

## 4. FBC-3: Recovery-to-Replan Contract

- **Input signals:** `recovery_used_streak`, `recovery_failed`,
  `post_recovery_H_min`, progress, QP status, and replanning availability.
- **Trigger:** repeated recovery, failed recovery with a safe holding option,
  unresolved post-recovery warning, or poor progress under repeated recovery.
- **Output action:** `replan_request = True` with a bounded risk summary and
  reason code to an external planner.
- **Assumptions:** a planner interface exists, accepts the declared message,
  and can return a valid nominal command; safe waiting is possible.
- **Assurance scope:** defines escalation from local recovery symptoms to an
  external route-level decision.
- **Non-claims:** does not implement a planner, guarantee a new route, or
  establish replanning quality.
- **Current status:** interface-level.

## 5. FBC-4: Safety-to-Risk-Cost Contract

- **Input signals:** low `current_h_min`, H-step minima, warning streak,
  recovery frequency, control deviation, QP infeasibility, and optional warning
  region/direction.
- **Trigger:** a configured weighted or rule-based combination of persistent
  low-margin and intervention signals.
- **Output action:** bounded `risk_cost`, confidence/status, and optional
  warning-region descriptor for an external planner.
- **Assumptions:** the external planner defines how the signal is normalized,
  spatially associated, aged, and combined with its own objective.
- **Assurance scope:** provides a safety-feedback quantity for future planner
  integration.
- **Non-claims:** does not prove risk-cost optimality, improve path-planning
  accuracy by itself, or define a complete planner objective.
- **Current status:** future planner integration.

## 6. FBC-5: Start/Goal-to-Waypoint-Screening Contract

- **Input signals:** start, goal, or candidate waypoint; map-frame validity;
  repository `h`; optional H-step screening result; and query validity.
- **Trigger:** low safety value, invalid frame, failed start/goal admission, or
  predicted short-horizon risk under the declared screening configuration.
- **Output action:** reject the candidate, set `unsafe_goal_flag`, and request
  an alternative waypoint, goal, or start.
- **Assumptions:** each candidate is expressed in the valid map frame and the
  safety query covers the candidate state; the external planner handles
  rejection.
- **Assurance scope:** interface-level candidate screening under the repository
  safety field and optional finite-horizon model.
- **Non-claims:** does not solve global planning, prove that accepted waypoints
  form a safe path, or validate planner completeness.
- **Current status:** future extension.

## 7. FBC-6: Deployment-to-Halt Contract

- **Input signals:** pose/frame validity, command-adapter validity,
  emergency-stop availability, rollout-adapter validity, solver status,
  recovery outcome, and safe-stop interface status.
- **Trigger:** invalid pose, invalid frame calibration, invalid command
  adapter, unavailable required emergency stop, QP failure without a usable
  response, or recovery failure.
- **Output action:** safe halt or abort, bounded stop command, fault reason, and
  operator/task notification.
- **Assumptions:** the robot-specific stop interface and stopping envelope are
  implemented and validated before physical execution.
- **Assurance scope:** specifies conservative fallback semantics for deployment
  integration.
- **Non-claims:** halt is a fail-safe policy, not a global safety proof or
  completed real-robot validation.
- **Current status:** deployment contract / interface-level.

## 8. Summary Table

| Contract | Input | Trigger | Feedback action | Current status | Non-claim |
| --- | --- | --- | --- | --- | --- |
| FBC-1 Verification-to-Command-Shaping | H-step warning/minimum, current margin, command limits | Warning or persistent low margin | Slowdown / conservative command bound | Interface-level / future extension | No planner optimality or current empirical gain |
| FBC-2 Verification-to-Recovery | H2/H3 warning, warning streak, recovery availability | Persistent or thresholded finite-horizon risk | Activate V4-C and re-verify | Implemented / supported in named V4-C reports | Not always-on MPC or globally optimal recovery |
| FBC-3 Recovery-to-Replan | Recovery streak/failure, post-recovery margin, progress | Repeated or failed recovery / poor progress | Replan request to external planner | Interface-level | Does not implement planner |
| FBC-4 Safety-to-Risk-Cost | Low `h`, warnings, recovery frequency, deviation, infeasibility | Persistent safety/intervention evidence | Risk-cost update | Future planner integration | No risk-cost optimality |
| FBC-5 Start/Goal-to-Waypoint-Screening | Candidate state, `h`, frame and optional rollout status | Unsafe/invalid candidate | Reject and request alternative | Future extension | Does not solve global planning |
| FBC-6 Deployment-to-Halt | Deployment validity, solver/recovery failure | Invalid required interface or unrecoverable failure | Safe halt / abort | Deployment contract / interface-level | Fail-safe policy, not global proof |

## 9. Level-1 Contract Reconstruction

Feedback contracts are reconstructed from existing events as candidate or
supported actions depending on evidence scope. Interface-level actions remain
interface-level. Reconstruction counts do not establish performance gains or
new controller behavior.

## 10. Level-2 No-Op Feedback Candidate Logging

Feedback contracts are logged as candidates in Level 2. Interface-level
candidates remain non-executed and do not modify control.

## 11. Level-3A Active Feedback Contract Status

The verification-to-command-shaping contract is instantiated as
warning-streak slowdown in Level 3A. Its claim scope is minimal active policy
smoke, not performance improvement.

## 12. Level-3B Targeted Activation Contract Status

The verification-to-command-shaping contract is tested under a targeted
natural-warning gate. Activation, if observed, supports warning-gated command
shaping only in the tested targeted case.

## 13. Level-3B-R Reproduction Reconciliation Status

The verification-to-command-shaping contract requires a naturally warning-rich
executable context before active testing. Level 3B-R diagnoses whether such a
context can be reproduced.

## 14. Fixed-Candidate Warning-Gated Slowdown Contract Status

The verification-to-command-shaping contract is exercised on the fixed C003
candidate only because natural warning was reproduced and slowdown was
triggered after the warning gate. This validates activation timing and command
scope, not performance improvement.

## 15. Level-3C Fixed-Case Feedback Comparison Status

The verification-to-command-shaping contract is compared against no-op
execution for fixed C003 only. The active path scales only the wrapper-level
executed command under a natural warning gate. The comparison is a targeted
behavioral observation and not evidence of generalized performance
improvement or benchmark-level warning reduction.

## 16. Level-3D Small-Cohort Feedback Comparison Status

The verification-to-command-shaping contract is compared against no-op
execution over a pre-registered small cohort. Observed differences remain
targeted cohort observations and must not be generalized.
