## Scope

Design-only continuation from Open Draft PR #95 (`l2-h1-shadow-frozen-replay-v1` at `a7fd936804284a299467f1bfcc76deab12fdf0c3`, base `l2-h1-shadow-certifier-v1`). No runtime collection, navigation, controller change, production instrumentation, or certifier mutation occurred.

## Frozen replay inputs

PR #95 exposed 6,853 records, 2,594 formally replayable (37.8520%), 4,259 missing numeric `u_k`, and 5,795 unknown reachability. L2 evaluated 788 records (770/18/0 PASS/FAIL/UNKNOWN); selected/executed candidates were 560/6 over 566 and non-executed candidates 210/12 over 222. Twenty native multi-candidate groups had 20/20 distinct H1 endpoints and 0/20 status disagreement. These are design inputs, not upgraded claims.

## Selected observation design

The frozen `run.py` control cycle makes `x_k`, nominal `u_des`, accepted selected `u_k`, and `dt` simultaneously visible after the solver-success guard and before plant propagation. The selected architecture places a future instrumentation-only immutable tap there. It performs `enqueue_nowait` to a bounded queue; an isolated worker runs frozen read-only L0/L1/L2 observation stages and appends results. There is no result return path or authority.

Compared options: post-commit tap (selected), wrapper/decorator (fallback), pure out-of-process log sidecar (insufficient with current fields), and post-plant log scraping (rejected for off-by-one/missingness).

The schema mandates same-decision IDs, `x_k/p_k/v_k/dt`, numeric selected `u_k`, selected and native candidate provenance, explicit L0/L1/L2 reachability, content-addressed map authority, tri-state L2 status, distinct instrumentation health, queue/drop records, and all authority flags false. Executed candidates form the primary cohort; pre-existing native non-executed candidates are secondary. Synthetic candidates are prohibited.

## Prospective analysis and stopping

Primary endpoint: selected/executed `PROSPECTIVE_L1_PASS_L2_FAIL` prevalence among explicitly reached/evaluated L2 observations. Secondary endpoints cover UNKNOWN, reach, completeness, native multi-candidate prevalence/disagreement, selected/non-selected status, backend, and trial heterogeneity. Rates always carry numerator and denominator. Instrumentation missingness is not L2 UNKNOWN.

The primary stopping plan freezes the full mature Stonehenge 100-trial indexed manifest and stops only after all trials are terminal. A fallback targets 566 L2-reached selected evaluations with the same 100-trial cap and only stops after the current trial, never by FAIL count. Trial-cluster bootstrap/trial-level aggregation replaces iid-step inference.

Future phases are: Phase 0 implementation QA, Phase 1 OFF-vs-ON equivalence, Phase 2 logging pilot, Phase 3 separately authorized fixed cohort, Phase 4 analysis. Pilot/equivalence data are excluded by default. Equivalence, logging, map authority, zero feedback, provenance, alignment, queue, and protocol-freeze gates are specified. None were executed here.

## Review and decision

Four independent design passes (control theory, robotics/systems, statistics/evaluation, software architecture/reproducibility) vote 4/4 for Case A with no critical blockers. Supported future claims remain signal/information/prevalence evidence only. Collision reduction, progress, controller efficacy, intervention success, recursive feasibility, deployment, real-time, and superiority claims are prohibited.

`FINAL_STATUS=PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_V1`

`FINAL_DECISION=FREEZE_ON_POLICY_SHADOW_PROTOCOL_AND_IMPLEMENT_NONINVASIVE_INSTRUMENTATION`

Only next task: `IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1` (not authorized or executed by this PR).
