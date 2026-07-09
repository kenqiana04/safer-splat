# Paper Insert: Feedback-Augmented Safety Assurance Framework

## 1. Introduction Insert

GSplat-based CBF filters provide instantaneous action correction, but
deployment-oriented safety requires the outputs of certification, filtering,
and verification to influence subsequent decisions. A feasible CBF-QP result
can coexist with a finite-horizon margin warning, repeated large command
interventions can indicate persistent conflict with the nominal route, and a
successful local recovery may still reveal that the route repeatedly enters a
low-margin region. Treating these signals only as passive diagnostics leaves
the assurance chain unable to express when execution should slow, recover,
request a different route, reject a target, or halt.

Our prior systematization identifies four deployment-relevant failure modes:
start-state unsafety, CBF-QP feasibility failure, sampled-data margin risk, and
recovery insufficiency. These modes naturally produce feedback signals:
Start-Safe supplies admission status, the CBF-QP supplies feasibility and
intervention status, H-step verification supplies predicted margin warnings,
and triggered recovery supplies response outcomes. The remaining challenge is
to convert this heterogeneous evidence into bounded actions without conflating
warning, infeasibility, recovery failure, and collision.

We address this architectural gap with the Safety-Assurance Feedback
Coordinator (SAFC), a contract-based supervisory layer that converts assurance
signals into command-shaping requests, recovery triggers, planner-facing
feedback, waypoint/goal rejection, or conservative halt. SAFC transforms the
minimal Start-Safe--filter--verify--recover chain into a feedback-augmented
assurance architecture while preserving a planner-agnostic boundary. It does
not implement a planner or localization method, replace the CBF-QP or V4-C,
claim a new CBF theorem, or establish a global safety guarantee.

## 2. Method Insert

SAFC receives six groups of signals: Start-Safe certification and repair
status; CBF-QP solver, active-constraint, and command-deviation status;
H1/H2/H3 verification minima and warning hysteresis; recovery activation,
success, failure, runtime, and post-recovery margin; nominal-command and
planner availability; and deployment-interface validity. A seven-state
supervisor separates pre-execution certification (S0), nominal filtering (S1),
verified execution (S2), warning-aware execution (S3), recovery (S4),
planner-facing replan request (S5), and safe halt (S6). Each transition invokes
a bounded feedback contract: a finite-horizon warning may request slowdown or
trigger recovery; repeated recovery or poor progress may request replanning;
low-margin/intervention evidence may be exposed as a planner risk-cost signal;
unsafe targets may be rejected; and invalid interfaces or unrecoverable
failure lead to a conservative halt. Warning exit uses a clear streak, every
successful recovery is re-verified, and no planner-facing response is treated
as successful until a valid external command is returned. The currently
supported path is verification-triggered V4-C behavior in named experiments;
general command shaping, replanning, risk-cost integration, waypoint screening,
and real-robot stopping remain interface-level or future extensions.

## 3. Contribution Insert

> We introduce a Safety-Assurance Feedback Coordinator that converts
> start-state certification, CBF-QP status, finite-horizon verification
> warnings, and recovery outcomes into bounded feedback actions. This
> transforms the safety layer from a linear monitor-filter-recover chain into a
> feedback-augmented assurance architecture while preserving planner-agnostic
> boundaries.

The contribution is architectural and contract-based: it defines signal
semantics, a fail-safe state machine, feedback contracts, and explicit
implemented/interface/future status. Empirical claims remain restricted to
existing tracked reports.

## 4. Discussion Insert

SAFC does not introduce a new path planner; it sends bounded evidence and
requests to an external nominal-command or planning interface. It does not
claim global safety because its inputs and actions remain conditioned on the
repository safety field, finite-horizon rollout, selected thresholds, solver
status, and deployment-interface validity. It also does not claim four-wheel
validation: pose, frame, command, rollout, and emergency-stop adapters require
separate physical implementation and testing. Planner-facing signals such as
`replan_request`, `risk_cost`, and waypoint rejection are therefore
architectural interfaces unless future experiments explicitly validate them.
The conceptual gain is a closed-loop account of how verification and recovery
evidence changes subsequent decisions, with every escalation tied to an
assurance contract and non-claim rather than presented as an unbounded
capability.

## 5. Reviewer-Facing Claim-Evidence Check

| Claim | Evidence | Status / required wording |
| --- | --- | --- |
| SAFC defines a feedback-augmented assurance architecture | Coordinator, state-machine, feedback-contract, and pipeline specifications | Supported as a theory/architecture contribution |
| H-step warning can trigger V4-C Recovery | Tracked V4-C reports | Supported only for named tested configurations |
| SAFC improves planner accuracy or optimality | No current planner integration experiment | Unsupported; do not claim |
| SAFC provides end-to-end global safety | No global theorem or complete deployment model | Unsupported; use module-level bounded assurance wording |
| SAFC is validated on a four-wheel robot | No completed robot adapter/experiment | Unsupported; describe interface contract and future validation |
| Replanning, risk-cost feedback, and waypoint screening are currently implemented | Contract-level files only | Unsupported as implementation; label interface-level/future |
