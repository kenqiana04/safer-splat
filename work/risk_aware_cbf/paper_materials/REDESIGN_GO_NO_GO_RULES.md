# Redesign Go / No-Go Rules

These rules prevent parameter sweeps and complexity growth from being
misrepresented as method redesign.

## Version-Level Stop Rule

A concrete version stops when all of the following are true:

1. The minimum prototype fails its predefined criterion.
2. Implementation correctness is confirmed.
3. No configuration mismatch explains the failure.
4. Measurement definitions are valid and do not confuse warning, collision,
   progress, runtime, or `h`.
5. The tested cases show no useful effect in their intended targeted scope.

Examples:

- VANS magnitude-only shadow v0 stops because 1/189 verified alternatives and
  0 progress-nonworse alternatives do not justify active promotion.
- FC-Aware V1 current branch stops because broader recovery-disabled flight20
  exposed collision in fixed and capped configurations and the branch is
  unsafe to expand.
- Primitive MPC-style recovery v0 stops because it leaves 96 selected margin
  violations in both H2 and H3 targeted replay.

## Mechanism-Family Stop Rule

A mechanism family stops only when all of the following are true:

1. At least two substantively different versions have been tested.
2. Both fail for the same structural reason.
3. Candidate space or interface constraints have been verified.
4. Further complexity would cross paper boundaries or require a planner.
5. A simpler bounded redesign no longer exists.

Not yet stopped:

- verification-aware selection: only magnitude-only VANS-v0 was tested;
- SAFC feedback: slowdown was tested, but supervisory mode selection was not;
- predictive recovery: primitive MPC-style failed, but V4-C is positive.

## Direction-Level Stop Rule

A research direction stops only when all of the following are true:

1. At least two or three orthogonal mechanism families have been tested.
2. Implementation and measurement have been validated for each.
3. Failures share a repeated structural cause.
4. No credible bounded redesign remains.
5. Expected contribution no longer justifies complexity.

Do not close a research direction after one failed implementation.

## Redesign Admission Rule

A redesign may enter a minimum prototype only if it:

- has a named hypothesis;
- differs mechanistically from failed versions;
- lists exact supported and unsupported claims;
- has a bounded candidate/action/mode set;
- can be falsified by a small smoke or targeted case;
- does not require full100 before smoke;
- does not hide negative evidence;
- does not call tuning a new method.

## Current Direction Decisions

- SAFC direction: open.
- Verification-aware selection direction: open.
- Current warning-streak slowdown version: diagnostic only.
- Current magnitude-only VANS-v0: diagnostic only.
- Current FC-Aware V1 branch: archived as diagnostic/ablation.
- Current primitive MPC-style recovery profile: archived as negative branch.
