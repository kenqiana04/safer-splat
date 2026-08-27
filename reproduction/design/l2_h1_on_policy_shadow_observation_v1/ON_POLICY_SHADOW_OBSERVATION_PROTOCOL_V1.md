# On-Policy L2/H1 Shadow Observation Protocol V1

## Status and scope

This is a prospective design frozen before collection. It does not collect data, integrate a controller, or claim performance. **DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.**

## Design inputs, not conclusions

PR #95 contained 6853 records, of which 2594 (37.8520%) were formally replayable. All 4259 non-replayable records lacked numeric `u_k`; 5795 had unknown reachability. Among 788 evaluated records, L2 was 770/18/0 PASS/FAIL/UNKNOWN. Executed candidates were 560/6 PASS/FAIL over 566; non-executed candidates were 210/12 over 222. The 20 multi-candidate groups had distinct H1 endpoints in 20/20 and status disagreement in 0/20. These historical rates are planning priors affected by missingness and source selection.

## Prospective unit and timing

Every accepted frozen-controller step is an intended observation unit. Capture occurs after selected `u_k` is committed by the frozen controller and before plant propagation. The tap copies the complete immutable payload and calls only a bounded `enqueue_nowait`. The isolated worker then evaluates the read-only L0/current, L1/immediate-segment, and L2/H1 stages and writes append-only results.

The shadow result has no consumer in the controller. FAIL, UNKNOWN, candidate disagreement, queue failure, and worker crash all leave the already selected action and future controller distribution unchanged.

## Reachability state machine

At worker runtime, each payload records explicit stage transitions rather than inferring them later:

1. L0/current-feasibility reached -> PASS/FAIL/UNKNOWN;
2. L1/immediate segment reached only under the frozen observer progression -> PASS/FAIL/UNKNOWN;
3. candidate preparation reached with a committed selected candidate;
4. L2 reached only when the frozen prerequisites are satisfied;
5. L2 evaluated -> PASS/FAIL/UNKNOWN.

The source class is always `SHADOW_PIPELINE_RUNTIME_OBSERVATION`. `L2_NOT_REACHED`, `L2_UNKNOWN`, `OBSERVATION_INCOMPLETE`, and `SHADOW_EVALUATION_DROPPED` are disjoint.

## Candidate policy

The selected/executed candidate is primary. All native candidates that existed before observation may be recorded as secondary. The `run.py` baseline contributes nominal `u_des` and selected `u`; a richer frozen runtime may expose a native alternative set. No rotation, noise, interpolation, perturbation, resampling, or library expansion is permitted. Candidate synthesis count is zero.

## Map authority

Before any future equivalence or collection run, a map manifest hashes every immutable artifact byte, representation contract, snapshot mapping, and robot/margin/rho contract. Static maps use one stable snapshot reference per run/trial; dynamic maps require a content-addressed snapshot per step. A scene name or path alone is never authority.

## Queue and failure behavior

Queue capacity is bounded and frozen by the future implementation protocol after Phase 0 measurement; this design intentionally does not invent a throughput number. Enqueue policy is nonblocking. Full/unavailable queues drop the observation, increment a monotonic counter where safely possible, and emit a minimal drop record. Sequence gaps are detected from `payload_sequence_id`. Worker heartbeat and shutdown-flush outcomes are logged. Shutdown may wait only outside the control cycle and may not retroactively change a trajectory.

## Prospective cohort and analysis

Primary cohort: every on-policy step for which the frozen controller committed a selected candidate, the zero-authority shadow progression records stored L1 PASS, L2 reached, and L2 formal evaluation PASS/FAIL/UNKNOWN. Primary mechanism endpoint: `P(L2_FAIL | stored_L1_PASS, L2_reached, selected/executed, L2_evaluated)`.

Secondary cohorts include all native candidates, non-executed native candidates, native multi-candidate groups, backend classes, L2 UNKNOWN, reachability, and logging completeness. They may not replace the primary executed rate.

## Prospective event

`PROSPECTIVE_L1_PASS_L2_FAIL` requires a true frozen-controller on-policy step, committed selected/executed candidate, stored runtime shadow L1 PASS, explicit L2 reach, formal L2 FAIL, and zero control feedback. It may be called a candidate-dependent future-safety shadow signal or L2-specific information increment. It is not a prevented collision, intervention success, avoided failure, control improvement, or safety gain.

## Phases (future only)

- **Phase 0:** implementation validation, schema/unit/static tests; no research data.
- **Phase 1:** paired OFF-vs-ON equivalence smoke on fixed seeds; QA only, excluded from primary cohort.
- **Phase 2:** logging-completeness pilot; excluded by default from primary cohort.
- **Phase 3:** frozen-manifest prospective shadow cohort; only after all gates pass.
- **Phase 4:** analysis only under the frozen denominator/statistical plan.

This task executes none of Phases 0-4.

## Claims boundary

The future cohort can describe signal prevalence, prospective L1 PASS/L2 FAIL information increment, UNKNOWN reliability, native certificate discrimination prevalence, logging completeness, and map-relative mechanism evidence. It cannot establish collision reduction, progress, efficacy, intervention success, recursive feasibility, safe stop, physical safety, deployment, real-time performance, or Core V2 superiority.
