# V4-C Module-Level Failure Mode Analysis

## Reading Rule

The entries below distinguish existing evidence from required future
measurement. A reported zero recovery failure in prior dense-flight runs is not
evidence that a failure mode cannot occur. No new data were generated here.

| ID | Failure mode | Current evidence | Required measurement | Category | Likely redesign direction | Future bounded experiment | Claim boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-V4C-1 | Candidate set has no feasible recovery | Not observed in reported H3_N128/R4 dense-flight summaries; fallback exists in code | Per activation feasible count and fallback source | Mechanism coverage | Add family-level feasibility accounting before enlarging any budget | Fixed hotspot replay with per-family aggregate only | No claim of universal feasibility |
| F-V4C-2 | Feasible recovery improves `h` but harms progress | Aggregate progress exists; safety-progress tradeoff by candidate is not measured | Selected and feasible-family progress delta conditioned on margin pass | Selection objective | Safety-progress Pareto selection | Small prespecified activated contexts | No claim that current cost preserves task progress |
| F-V4C-3 | Repeated activation causes excessive runtime | Supported: H3_N128 cost is concentrated on activated trials; prior report identifies repeated activation as dominant overhead | Activation streak, recovery runtime per step, and recurrence histogram | Mechanism/runtime | Severity-aware trigger and hierarchical evaluation | Bounded hotspot runtime audit | Runtime concentration is configuration-specific |
| F-V4C-4 | Random budget dominates runtime without useful selections | Plausible from 128 random sequences; selection contribution is not measured | Generated/selected/unique-success counts and runtime by family | Implementation instrumentation gap | Hierarchical evaluation or fixed adaptive family budget | Family-contribution audit | Do not claim random candidates are redundant yet |
| F-V4C-5 | H3 success fails later in closed loop | Not observed in reported dense-flight summaries, but current recovery success is horizon-local | Post-recovery H1/H2/H3 status, later warning/collision and recurrence windows | Mechanism horizon limitation | Persistent-warning memory and post-recovery verification | Bounded replay with delayed outcome aggregation | Horizon success is not route-level success |
| F-V4C-6 | Same warning context recurs | Repeated activation is observed; geometric/context identity recurrence is not measured | Context key, recovery streak, selected family, and post-recovery warning recurrence | Mechanism memory gap | Persistent-warning recovery memory | Fixed recurrent hotspot contexts | Do not infer identical geometry from activation count alone |
| F-V4C-7 | Weighted cost selects feasible but task-inefficient candidate | Not measured; code uses a scalar weighted objective | Pareto frontier, rank disagreement, and progress regret among feasible candidates | Objective-design risk | Pareto recovery selection | Candidate-level shadow audit | No claim that a different cost is better |
| F-V4C-8 | Family is redundant or never selected | Not measured because family-level aggregates were not retained | Family generated/feasible/selected/unique-success rates | Instrumentation gap | Remove/defer redundant family only after audit | Candidate-family audit | No family removal is justified now |
| F-V4C-9 | Trigger is early, late, or too sensitive | `on_margin_violation` limits activation; no comparative trigger study exists | Severity bins, false activation proxy, missed-risk proxy, and activation latency | Trigger-design risk | Trigger-severity-aware recovery | Bounded fixed-context trigger comparison | No optimal trigger threshold claim |
| F-V4C-10 | Recovery cannot address stalling/no completion | Current reports show local margin repair, not route planning or completion proof | Completion, stall duration, distance-progress and repeated-recovery relation | Scope/mechanism boundary | Escalate an unresolved outcome to a planner-facing interface, outside V4-C | Separate interface study only | V4-C is not a planner and cannot claim completion repair |

## Consequence

The clearest supported design pressure is F-V4C-3: costly repeated candidate
evaluation. F-V4C-4, F-V4C-7, and F-V4C-8 require family/selection telemetry
before deciding whether random candidates or scalar cost are the root cause.
F-V4C-5, F-V4C-6, and F-V4C-10 are deliberately not collapsed into a local
recovery-success metric.

## R-V4C-1 Held-Out Evidence

The held-out flight H3_N128 cohort directly supports F-V4C-3: original activated-step median evaluation time was 8.00 s versus 1.64 s for hierarchical V0. F-V4C-4 is not resolved as a general claim: random was selected zero times and had zero unique-feasible contexts in this cohort, while Stage B entered 34 contexts and reproduced original failures. This is bounded evidence, not authorization to remove random families or change the original cost.
