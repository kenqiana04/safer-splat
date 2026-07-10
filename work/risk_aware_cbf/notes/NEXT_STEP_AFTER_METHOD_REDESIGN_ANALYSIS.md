# Next Step After Method Redesign Analysis

## If One Redesign Is Selected

Create a bounded prototype task for Verification-Aware Supervisory Mode
Selection.

Exact mechanism:

- fixed rule-table selector among original `u_safe`, warning-gated slowdown,
  existing V4-C recovery, and safe halt;
- no waypoint generation;
- no route optimization;
- no new dynamics;
- no CBF-QP modification.

Exact interface:

- H1/H2/H3 warning flags and margins;
- CBF-QP feasibility/status;
- current formal state and original `u_safe`;
- V4-C recovery availability;
- slowdown eligibility;
- safe-halt condition.

First execution ladder:

1. Write mode table and falsification rule.
2. Run one shadow audit over existing targeted contexts.
3. If shadow passes, run one active smoke on one target case.
4. Stop before cohort unless the smoke passes.

Predefined stop rule:

- stop if the selector never chooses a useful non-slowdown mode;
- stop if selected modes fail H-step verification;
- stop if implementation requires planner semantics;
- stop if state isolation or command-scope checks fail.

## If No Redesign Is Credible

Close only the failed version or mechanism family that met the stop rule.

Record:

- versions tested;
- structural reason;
- evidence;
- future-work boundary.

Do not close SAFC or verification-aware selection unless the direction-level
stop rule is met.

## Prohibited

- automatic paper drafting;
- arbitrary parameter sweep;
- hiding negative evidence;
- calling tuning a new method;
- full100 before smoke;
- abandoning a direction after one failed version.

## Immediate Recommendation

Proceed to a separate bounded task for R1 only if the next task explicitly
asks for a prototype. This analysis task itself runs no experiments and
implements no Python.
