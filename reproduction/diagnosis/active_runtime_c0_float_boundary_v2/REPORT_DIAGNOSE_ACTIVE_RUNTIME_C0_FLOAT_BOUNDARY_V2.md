# Diagnose Active Runtime C0 Float Boundary and Early Terminal V2

## Answer-first conclusion

The five cycle-0 rejections are explained by a float32 actuator-boundary canonicalization gap. In every affected trial, the frozen CBF-QP returned a lawful `PRIMARY_NATIVE_CBF_QP` candidate containing `-0.10000000149011612` and, in trial 85, also `0.10000000149011612`. These are exactly `float(np.float32(-0.1))` and `float(np.float32(0.1))`. `PrimaryProposalAdapter` preserved those source values while promoting them to Python floats; C0 then compared them strictly against Python `[-0.1, 0.1]` and returned `FAIL / F_ACTUATOR_ADMISSIBILITY_LOCAL`.

All seven offending components are class A (`EXACT_FLOAT32_BOUNDARY_REPRESENTATION`); none is class B and none is a true class-C violation. Maximum apparent excess is `1.4901161138336505e-09`, below one float32 ULP near 0.1 (`7.450580596923828e-09`). No PR #134 result is changed.

`FINAL_STATUS=PASS_DIAGNOSE_ACTIVE_RUNTIME_C0_FLOAT_BOUNDARY_V2`

`ROOT_CAUSE=FLOAT32_ACTUATOR_BOUNDARY_CANONICALIZATION_GAP`

`FINAL_DECISION=REPAIR_PRIMARY_CANDIDATE_ACTUATOR_BOUNDARY_CANONICALIZATION_V2`

## Evidence and bounded probe

PR #134 was independently verified as Open Draft, branch `active-runtime-pilot-v2`, head `866975b5b3551eaa0111bbf910bbfb7dc80ac69e`. Its 10/10 pairs and 20/20 eligible arms remain frozen, including C0 PASS/FAIL/UNKNOWN = 598/5/0 and failing trial IDs 5, 25, 45, 75, 85. Diff from its direct base contains no runtime or production-source change.

PR #134 did not persist the rejected P0 candidate itself. The protocol-authorized fallback was therefore used once: the exact frozen source checkout, map, initial states, goals, desired-control formula, and CBF-QP were evaluated for one P0/C0 step in each of the ten trials. It made zero plant calls, zero oracle calls, and zero episode rollouts; GPU 1 was clean afterward. Every reconstructed candidate matched the corresponding frozen Reference step-0 action exactly.

## Static C0 proof

The frozen branch order in `c0_admission.py:15-23` is:

1. nonfinite or wrong dimension → `UNKNOWN / CANDIDATE_NONFINITE_OR_WRONG_DIMENSION`;
2. state or map mismatch → `UNKNOWN / CANDIDATE_STATE_OR_MAP_IDENTITY_MISMATCH`;
3. unlawful source → `FAIL / SOURCE_INVALID`;
4. any strict `value < low or value > high` → `FAIL / F_ACTUATOR_ADMISSIBILITY_LOCAL`;
5. otherwise → `PASS / C0_PASS`.

The bounds are inclusive conceptual Python floats `(-0.1, -0.1, -0.1)` and `(0.1, 0.1, 0.1)`. `primary_proposal_adapter.py:27-30` converts the solver output with `tuple(float(value) for value in raw)` and creates `PRIMARY_NATIVE_CBF_QP`. `runtime_types.py:283-287` marks that source lawful and binds the exact state and map identities. All ten probes had matching identities and lawful provenance.

## Failing and passing boundary values

| Trial | Frozen/replayed first candidate | C0 |
|---:|---|---|
| 5 | `[-0.10000000149011612, -0.10000000149011612, 0.0031727957539260387]` | FAIL |
| 25 | `[0.0621945783495903, -0.10000000149011612, 0.015800148248672485]` | FAIL |
| 45 | `[0.09999999403953552, -0.10000000149011612, 0.028173254802823067]` | FAIL |
| 75 | `[-0.10000000149011612, 0.09999999403953552, 0.04582265391945839]` | FAIL |
| 85 | `[-0.10000000149011612, 0.10000000149011612, 0.051367729902267456]` | FAIL |

Passing controls expose the other side of the representation boundary: trials 15 and 35 contain `±0.09999999403953552`, while trials 55 and 65 contain slightly more interior float32 values. They are visually close to ±0.1 but remain within Python bounds. Trial 95 has no boundary component. This explains why strict comparison partitions otherwise analogous source-float values.

## Reference comparability and causal chain

For all five affected trials, Reference executed the exact same CBF-QP first action and continued for 51–333 steps, with positive normalized progress from 0.06685 to 0.85314. All five Reference arms had zero represented-map collision-proxy trials and zero certification-margin-violation trials. The Active cycle-0 evidence shows L1 PASS, P0 PASS, C0 actuator-admissibility FAIL, no L2 or L3 evaluation, no retained backup, no native alternative, a routed `ELIGIBLE_CURRENT_CERTIFIED_TERMINAL_ACTION`, one certified-terminal commit, `NATIVE_NOT_MOVING`, and progress 0.

Therefore C0 rejection is the root event. No retained backup at cycle 0, empty native-alternative inventory, initial zero velocity, and terminal eligibility are downstream amplifiers. They do not explain the C0 rejection itself. L1 PASS for every affected initial state, positive post-hoc clearances, and Reference progression under the same map/task establish `MAP_TASK_DIFFICULTY_NOT_PRIMARY_EXPLANATION_FOR_THE_FIVE_CYCLE0_C0_REJECTIONS`.

## Repair options, without implementation

Option A is the minimal recommendation: at the source-boundary canonicalization owner, convert only a component exactly equal to the source float32 representation of a frozen bound to its conceptual ±0.1 value. This preserves the frozen bounds and strict C0 semantics and must not clip any other value.

Option B, a ULP-aware C0 comparison, changes C0 comparator semantics and is broader than the observed cause. Option C, adding actuator box constraints to the QP, is unjustified here because no true beyond-one-ULP violation was observed.

The repair task must add targeted boundary and true-out-of-bound regressions, test the five affected and five passing controls, run a small smoke, rerun only the ten Active Pilot arms, reuse PR #134's ten frozen Reference arms, and not run official100.

## Evidence boundary

This is a post-hoc numeric admission diagnosis. It does not establish collision reduction, progress improvement, performance superiority, deployment readiness, or the outcome of any repaired runtime. Runtime, controller, CBF, Supervisor, terminal policy, actuator bounds, map, geometry, deadline, and oracle were not modified.

Only next task: `REPAIR_PRIMARY_CANDIDATE_ACTUATOR_BOUNDARY_CANONICALIZATION_V2`.
