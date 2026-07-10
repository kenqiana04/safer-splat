# SAFC Design Space Map

SAFC is a supervisory safety-assurance layer, not a planner. Its feedback
actions must be bounded and must respect the CBF-QP, dynamics, planner, and
deployment boundaries unless a later task explicitly justifies crossing one.

| Action | Pre/post CBF position | Changes magnitude? | Changes direction? | Requires planner? | Requires new dynamics? | Already implemented? | Evidence | Expected benefit | Failure risk | Paper-boundary risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no-op execution | post-CBF observation only | no | no | no | no | yes | Level 2 no-op and baseline runs | Establish passive instrumentation and equivalence | No active mitigation | low |
| warning-streak slowdown | post-CBF wrapper execution | yes | no | no | no | yes | Levels 3A-3E | Reduce exposure after warnings | Cannot change direction; mixed outcomes | low if claims bounded |
| bounded hold / pause | post-CBF wrapper execution | yes, to zero or near-zero | no | no | no | no | not tested | Stop motion during persistent warning | May stall or increase exposure | medium |
| triggered predictive recovery | post-verifier recovery mode | yes | yes, through sequence choice | no full planner | no | yes, V4-C | V4-C H3_N128 and R4_H2_N64 | Remove executed horizon margin violations | Runtime overhead; sampling assumptions | medium |
| safe halt | deployment/supervisory boundary | yes, to halt | no | no | no | contract only | feedback contracts | Conservative response to invalid interfaces or unrecoverable risk | Completion loss | low if not called safe execution |
| replan request interface | planner interface | no direct command | planner decides | yes, external | no | specified only | interface docs | Escalate repeated local safety symptoms | Becomes planner integration | high |
| nominal command rejection | pre-CBF admission | yes, rejects source | no replacement unless fallback exists | maybe | no | not implemented | contract-level only | Avoid feeding unverifiable commands | Requires source policy or halt fallback | medium |
| mode selection among existing bounded actions | supervisory layer over existing modes | yes, through chosen mode | only if choosing V4-C recovery | no new planner | no | not yet as integrated policy | component evidence exists separately | Select original, slowdown, V4-C, or halt based on verifier evidence | Wrong mode selection; runtime overhead | medium-low |
| verification-aware recovery trigger | verifier-to-recovery gate | no direct command | recovery may | no | no | partly via V4-C activation | V4-C reports | Use H-step evidence to trigger recovery only when needed | Over/under-triggering | medium-low |
| verification-aware action source selection | pre-CBF nominal source | maybe | maybe | no if bounded sources | no | VANS shadow v0 only | VANS action audit | Choose more verifiable input action | Can become local planner | medium-high |

## Verification-Aware Supervisory Mode Selection

This is the most credible next SAFC redesign because it chooses among modes
that already exist or are already contracted:

- execute original CBF-filtered command;
- apply warning-gated slowdown;
- invoke existing V4-C recovery;
- safe halt.

It is not a local planner because it does not generate waypoints, optimize a
route, create new trajectories, or change the dynamics. Its design question is
which already verified bounded mode should be active under the current
assurance state.

Minimum interface:

- current state and filtered command;
- H1/H2/H3 warning flags and margin values;
- CBF-QP feasibility/status;
- V4-C recovery availability and estimated cost;
- slowdown eligibility;
- halt condition.

Primary risk:

- mode selection can hide weak action mechanisms behind complexity. The first
  prototype must have a small fixed rule table and a falsification rule.
