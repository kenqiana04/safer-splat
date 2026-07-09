# Closed-Loop Safety Assurance Pipeline

## 1. From Linear Chain to Feedback Loop

The original minimal assurance chain is:

```text
Start-Safe -> CBF-QP -> DT Verification -> Triggered Recovery -> Execution
```

This chain defines admission, filtering, verification, and optional response,
but its warning and outcome signals can remain local to each stage. The
feedback-augmented architecture makes those signals supervisory inputs:

```text
Start-Safe / CBF-QP / DT Verification / Recovery
    -> SAFC
    -> command shaping / recovery / replan / risk-cost / waypoint rejection / halt
    -> execution or external planner interface
```

The architectural change is conceptual and contract-based. The current main
method supports Start-Safe, CBF-QP, DT Verification, and named
verification-triggered V4-C behavior. Planner feedback, general command
shaping, waypoint screening, and real-robot halt integration remain
interface-level or future extensions unless later experiments explicitly
validate them.

## 2. ASCII System Diagram

```text
                    ┌─────────────────────────────────────────┐
                    │ Safety-Assurance Feedback Coordinator   │
                    │ Inputs: start status, QP status, h_min, │
                    │ H-step warnings, recovery outcomes,     │
                    │ deployment-interface validity           │
                    │ Outputs: slowdown, recovery trigger,    │
                    │ risk-cost update, replan request, halt  │
                    └───────────────────┬─────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ↓                               ↓                               ↓
Nominal command shaping          Planner feedback              Recovery / Halt
        ↓                               ↑                               │
        └──────→ CBF-QP → DT Verification ─────→ Triggered Recovery ────┘
                         ↑                                      │
                         └──────── post-recovery verification ───┘
```

The external planner and deployment adapter remain outside the currently
validated simulation core. Their arrows represent declared interfaces, not
implemented planner or robot results.

## 3. Module Roles

| Module | Role | Feedback produced | Feedback consumed | Current status |
| --- | --- | --- | --- | --- |
| Start-Safe | Certify, repair, verify, or reject the initial state | Certification, repair, distance, initial `h`, start feasibility | Start/goal selection and task admission | Current main method / tracked evidence |
| CBF-QP | Filter `u_nom` into `u_safe` under current constraints | Solver status, active constraints, control deviation, current `h` | Recovery/halt escalation and intervention monitoring | Baseline current component |
| DT Verification | Evaluate finite-horizon sampled-data margin | H1/H2/H3 minima, warnings, warning/clear streaks | Slowdown, recovery trigger, replan escalation | Current main method / tracked evidence |
| Triggered Recovery | Select an alternative bounded action under warning | Use/success/failure, runtime, selected action, post-recovery margin | Replan request, halt, post-recovery verification | Optional current method; supported in named V4-C reports |
| SAFC | Aggregate signals and apply state/contract policy | Supervisory action, reason, state, validity | Signals from all assurance and deployment modules | Theory/architecture; only specific sub-paths currently supported |
| External Planner | Generate route, waypoint, goal, or nominal command | New nominal command and availability | Replan, risk-cost, rejection, warning-region signals | External interface / future integration |
| Real-Robot Adapter | Map state and command interfaces to physical platform | Validity, latency, stop status, executed command | Safe command, halt, rollout and frame requirements | Future real-robot validation |

## 4. Implemented vs Interface vs Future Work

| Mechanism | Status | Evidence / file | Paper wording |
| --- | --- | --- | --- |
| Start-Safe certification / repair | Current main method | Existing StartGuard, V4-A, and synthetic initial-unsafe reports | Repository-scoped start certification and repair under full-query validation |
| CBF-QP filtering | Baseline current component | Baseline navigation-stack audit and existing source | Existing instantaneous safety-filter interface |
| H-step DT Verification | Current main method | `REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md` | Finite-horizon sampled-data margin verification; warning is not collision |
| Verification-triggered V4-C Recovery | Optional current method / supported | V4-C recovery and full100 reports | Triggered empirical recovery in named tested configurations |
| SAFC S0-S6 supervisor as a whole | Architecture interface | `SAFC_STATE_MACHINE_SPEC.md` | Proposed contract-based feedback coordinator; not yet an end-to-end experimental module |
| Command slowdown / shaping | Interface-level / future extension | FBC-1 specification | Bounded command-shaping interface for future validation |
| Replan request | Architecture interface | Planner interface and FBC-3 | Feedback request to an external planner, not a planner implementation |
| Planner risk-cost update | Future planner integration | Planner interface and FBC-4 | Risk-cost signal for future integration; no optimality claim |
| Waypoint/goal screening | Future extension | Planner interface and FBC-5 | Safety-guided candidate screening interface |
| Deployment-to-halt | Deployment contract | Real-robot interface contract and FBC-6 | Required conservative fallback before physical validation |
| Four-wheel/real-robot validation | Future work | `REAL_ROBOT_INTERFACE_CONTRACT.md` and deployment plan | Not currently implemented or validated |
