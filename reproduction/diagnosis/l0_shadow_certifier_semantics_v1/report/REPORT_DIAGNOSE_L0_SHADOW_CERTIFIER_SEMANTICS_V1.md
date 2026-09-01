# REPORT — Diagnose L0 Shadow Certifier Semantics V1

## Direct answers

1. **Is the real L0 outcome observable?** Yes. The frozen per-step formal result logs retain `l0_status` and `l0_reason`; the later canonical analysis table drops both fields.
2. **L0 counts:** `PASS=0`, `FAIL=14,122`, `UNKNOWN=0`, `OTHER=0`.
3. **Reason distribution:** `FROZEN_L0_CURRENT_MAP_QUERY=14,122`. This is the exact logged reason, not a newly invented taxonomy mapping.
4. **Is adapter PASS mapping correct?** Yes. The formal L0 closure emits literal `PASS/FAIL/UNKNOWN`, and the adapter validates those literals and advances only on exact `PASS`. No enum/string/boolean mismatch was found.
5. **Frozen L0 semantics:** a current-state represented-map query on `p_k`; non-`FINITE` query status is `UNKNOWN`, otherwise `h>=0` is `PASS` and `h<0` is `FAIL`. The formal closure does not evaluate an immediate segment, candidate residual, or repair.
6. **Should the L0 gate block shadow L1/L2?** Under the frozen worker progression, yes. This is separate from controller authority: `u_k` was already committed, the shadow result has no controller consumer, and L0 FAIL changes no control action.
7. **Root class:** `L0-S2_TRUE_L0_FAIL_SUPPORT`.
8. **Causal chain:** `14122 committed steps -> 14122 typed L0 FAIL outcomes -> L0_BLOCKED -> L1/L2 NOT_REACHED -> N_primary=0`.

## Frozen identity and routing

PR #103 remained Open Draft at exact head `0b8e38e584c112eb778208e5c5933deb6adb23d0`. Its input lock and all frozen protocol/collection/analysis/post-reveal identifiers matched the task instruction.

PR #103's handoff named `DIAGNOSE_L1_SHADOW_CERTIFIER_SEMANTICS_V1`. Because the frozen evidence proves L1 executed zero times, this task corrects only the new-task routing to L0. PR #103 and V1 Case C remain unchanged.

## Observability audit

One formal result record was read only to enumerate keys and types. It contains typed string fields `l0_status`, `l0_reason`, and `l0_observation_source`, together with immutable payload hashes, map authority, and decision/trial/step identifiers. It does not contain raw map-query status, raw `h`, or a dedicated `l0_backend` field.

The canonical analysis builder copies L1/L2 fields but not L0 fields. Therefore PR #103's compact canonical recovery could correctly establish `L0_BLOCKED=14,122` but could not recover the underlying FAIL/UNKNOWN mix. The original frozen formal result artifacts can.

## Single streaming aggregation

The task-local script read the 100 frozen `shadow_certificate_result_log.jsonl` files once, line by line. It emitted only compact counts. It did not print or copy raw records and did not call the map, controller, or certifiers.

The accounting identity is exact:

`0 PASS + 14,122 FAIL + 0 UNKNOWN + 0 OTHER = 14,122 formal result records`.

The only logged L0 reason is `FROZEN_L0_CURRENT_MAP_QUERY`. Because that reason is used for both finite PASS and finite FAIL in the closure, it does not identify the geometric or map-level cause of negative `h`.

## Status mapping

`build_real_frozen_adapter.l0` converts the raw query status to its `.value` when available. Any token other than `FINITE` produces `UNKNOWN` with the original query reason; a finite query produces literal `PASS` when `float(query.h) >= 0.0`, otherwise literal `FAIL`.

`ReadOnlyFrozenCertifierAdapter.evaluate` accepts only `PASS`, `FAIL`, or `UNKNOWN`; any other token raises `INVALID_L0_STATUS`. It compares directly with `PASS`. Thus a `SAFE`, `ADMISSIBLE`, boolean, or enum object cannot silently masquerade as this formal PASS path. Exceptions also do not default to non-PASS; they exit worker evaluation and would not create the observed result records.

Every non-PASS outcome is deliberately collapsed only for downstream reachability to `L0_BLOCKED`, while the original typed `l0_status` remains in the formal result record.

## Frozen L0 semantics

The formal L0 closure is a direct subset of the broader frozen current-feasibility interface. It checks the committed step's current position `p_k` against the frozen map authority with FULL query scope. It does not use `u_k`, propagate an H1 segment, attempt repair, or execute L1/L2 mathematics.

The broader current-feasibility source distinguishes snapshot mismatch, unknown/nonfinite/error query states, negative-`h` infeasibility, and optional candidate residual. Those finer categories were not persisted by this formal L0 closure. Consequently this task establishes true FAIL support but not the deeper reason all 14,122 finite queries had `h<0`.

## Controller authority versus shadow observability

The controller commits `u_k` before the immutable observation is enqueued. The worker then runs the L0/L1/L2 reachability state machine. The shadow result has no feedback path and cannot modify the current or future controller trace.

Accordingly:

- controller-authority L0 gate: `NOT_REQUIRED` for this shadow task;
- worker-side shadow-observation L0 gate: `REQUIRED` by the frozen progression;
- implementation: `CONFORMANT` with that separation.

This conclusion does not claim control efficacy or prescribe a revised architecture.

## Historical bridge and limitations

No PR #95 historical bridge was read. The prospective result status is directly observable and its mapping is unambiguous, so historical evidence is unnecessary.

Unresolved evidence is narrow but important: raw query `h`, raw query status per record, and a typed failure reason finer than `FROZEN_L0_CURRENT_MAP_QUERY` were not logged. This task therefore does not attribute the universal FAIL result to map scale, radius, margin, coordinate frame, pose, geometry, or implementation error.

## Validation and boundary

- synthetic tests: 5/5 pass
- formal result schema records inspected: 1
- full result streaming scans: 1
- new experiments/navigation/GPU use: 0
- runtime/upstream/V1 mutations: 0
- raw logs committed: 0
- historical scientific result reinterpretations: 0

`FINAL_STATUS=PASS_L0_SHADOW_CERTIFIER_SEMANTICS_DIAGNOSIS_V1`

`FINAL_DECISION=FREEZE_L0_ROOT_CAUSE_AND_AUTHORIZE_TARGETED_CORRECTION_OR_DIAGNOSIS`

Only next task: `DIAGNOSE_L0_START_SAFE_FAILURE_SEMANTICS_V1`. It was not executed here.
