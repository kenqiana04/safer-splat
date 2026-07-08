# Experiment Matrix

## Simulation Experiments

| Experiment | Purpose | Baseline | Our method | Metrics | Current status | Missing items |
|---|---|---|---|---|---|---|
| Original closed-loop baseline | Establish SAFER-style GSplat CBF-QP behavior | official `run.py` / CBF-QP | none | collision, success, min h, runtime, QP feasibility | available from prior reproduction | no new run in this task |
| Start-Safe repair / certification | Detect and repair unsafe starts before rollout | original start state | feasibility check, verified projection, active-set projection | repair success, full-query verification, repair distance | completed in prior work | none for current report |
| DT Verification audit | Detect sampled-data H-step risk | executed baseline trajectory | H1/H2/H3 min h and margin flags | margin violation count, collision count, h trends | completed in prior work | distinguish warning from collision in writing |
| V4-C Recovery comparison | Reduce H-step warnings with triggered recovery | baseline CBF-QP action | triggered predictive recovery | collision, QP infeasible, base vs exec margin violations, runtime | pilot completed in prior work | no new V4-C experiment in this task |
| Adaptive V1 diagnostic | Test risk-response candidate scheduling | fixed candidate budget | adaptive selected_K schedule | candidate counts, runtime, safety, forced candidates | frozen / downgraded | do not claim runtime improvement |
| FC-Aware diagnostic / targeted ablation | Audit forced heading candidate bottleneck | fixed heading candidates | capped / ranked heading candidates | recall, candidate ratio, collision, stop reason | frozen after flight20 trial0 stop | do not enter full100 without redesign |
| MPC-style negative diagnostic | Test primitive-sequence recovery | V4-C / baseline recovery | MPC-style primitive sequences | success, collision, runtime, failure mode | negative diagnostic | future work only |

## Real-Robot Experiments

| Scene | Purpose | Required hardware | Required software interface | Metrics | Expected figure/table | Risk | Priority |
|---|---|---|---|---|---|---|---|
| start-near-obstacle | Demonstrate pre-execution start safety certification | mobile base, mapped obstacle, emergency stop | pose source, GSplat frame transform, start h query | start h, reject/repair/stop decision, emergency stop count | start-state table and photo | calibration error near obstacle | high |
| narrow passage | Demonstrate command filtering near close geometry | mobile base, narrow obstacle layout | nominal command input, safe command output, h query | intervention count, min distance/proxy h, completion time | trajectory overlay and command plot | physical collision if speed too high | high |
| obstacle-near-goal / close pass | Demonstrate safety layer under goal attraction | mobile base, close goal-side obstacle | goal command source, command adapter | final goal distance, interventions, h trend | goal-side close pass plot | getting stuck near obstacle | medium |
| DT-warning / recovery demo | Demonstrate triggered recovery under short-horizon risk | mobile base, controlled risk scene | H-step rollout, recovery command, logging | DT warning count, recovery count, post-recovery h | warning/recovery timeline | false recovery or late stop | high |

## What Is Required Before Running Real Robot

1. Confirmed robot command interface.
2. Confirmed localization / pose source.
3. Map-to-robot frame alignment procedure.
4. Physical obstacle setup with measured dimensions.
5. Emergency stop and safety operator.
6. Low-speed command limits.
7. Data logging for pose, nominal command, safe command, h, warnings, recovery, and stop reason.
8. Clear test protocol for aborting failed runs.
9. A statement that real-robot demos validate deployment feasibility, not global safety.

## Reporting Rules

- Report collision separately from margin violation.
- Report h as safety-function value, not meter clearance.
- Do not compare against full real-world planner benchmarks unless such baselines are actually implemented.
- Keep frozen branches in diagnostic tables.
- Keep real-robot demos separate from simulation benchmark claims.
