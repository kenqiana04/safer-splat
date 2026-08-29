# Report: L2/H1 shadow logging completeness pilot V1

## Technical summary

**PASS_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1 — CASE_A.** Exactly five preregistered `WRAPPER_ON` Stonehenge pilot runs completed once each. The independent committed-control/plant denominator contained **732** intended steps; captures, terminal shadow results, and uniquely joinable records were **732 / 732 / 732**.

This is a logging/evidence qualification result only. It is not an L2 efficacy, safety, prevalence, collision, progress, runtime, or real-time result. All rows are `PILOT_QA_ONLY` and permanently excluded from the formal prospective cohort.

## All six completeness gates reached 100%

| Gate | Rate | Verdict |
|---|---:|---|
| `capture_completeness` | `1.000000` | PASS |
| `selected_u_completeness` | `1.000000` | PASS |
| `map_authority_completeness` | `1.000000` | PASS |
| `reachability_completeness` | `1.000000` | PASS |
| `shadow_result_completion` | `1.000000` | PASS |
| `join_completeness` | `1.000000` | PASS |

The equality of all six rates is best represented as an exact audit table rather than a chart: every metric has the same target and observed value, so a plotted visual would add no discriminating information.

## Scope and denominator were frozen before collection

- Upstream PR #98 head: `b47b0e924804e3e446b1f9c184ee5ea5d268d613`
- Trial IDs: `[10, 30, 50, 70, 90]`
- Selection: `floor((j+0.5)*N/K), j=0..4, N=100, K=5`; frozen before results; no replacement
- Runs: `5 WRAPPER_ON`, fresh process, serial, retry count zero
- Environment identities: `1`; map identities: `1`

`N_intended_steps` comes from the independent committed-control/plant trace, not from capture JSONL. Each intended row requires a selected control aligned with the plant input plus plant input/output state facts. The official trial ID remains in the run manifest and trace; the frozen wrapper's process-local `trial-000000` token is joined through `run_id` and the complete runtime ID set.

## Every specified instrumentation error remained zero

| Error gate | Count | Verdict |
|---|---:|---|
| `N_queue_drop` | `0` | PASS |
| `N_serialization_error` | `0` | PASS |
| `N_worker_exception` | `0` | PASS |
| `N_worker_unavailable` | `0` | PASS |
| `N_alignment_failure` | `0` | PASS |
| `N_schema_failure` | `0` | PASS |
| `N_map_authority_failure` | `0` | PASS |
| `N_shutdown_incomplete` | `0` | PASS |
| `N_sequence_gap` | `0` | PASS |
| `N_duplicate_payload` | `0` | PASS |
| `N_duplicate_result` | `0` | PASS |

- `N_orphan_result` = `0`
- `N_capture_without_result` = `0`
- `L2_UNKNOWN_count` = `0` (descriptive only; no efficacy interpretation)

## Streaming aggregation and robustness checks

The aggregator streamed the five capture, result, and health logs, recomputed semantic hashes, and checked sequence uniqueness and eight-way capture/result identity alignment. Raw artifact bytes were hashed into the server manifest and were not copied into Git. A first task-local aggregation incorrectly assumed the process-local trial token equaled the official trial ID; that false join failure was preserved server-side, the join key was corrected to the frozen runtime schema, and no rollout or instrumentation was rerun or modified.

## Integrity and zero-authority boundaries passed

- Independent denominator resolved: `True`
- Join integrity: `True`
- Sequence integrity: `True`
- Instrumentation health separated from L2 UNKNOWN: `True`
- Controller/instrumentation mutation: `0 / 0`
- Controller intervention/candidate replacement: `0 / 0`
- Formal cohort/performance/runtime metric counts: `0 / 0 / 0`
- Raw logs committed to Git: `0`; server root: `/disk1/zlab/maintenance_records/l2_h1_shadow_logging_completeness_pilot_v1/server_execution`

## Limitations and claim boundary

Five QA runs establish bounded logging completeness under this frozen Stonehenge environment only. They do not estimate L2 signal prevalence or efficacy and do not establish collision reduction, progress improvement, runtime performance, real-time suitability, deployment safety, or completeness under future code/environment changes.

## Decision and next step

- `FINAL_STATUS=PASS_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1`
- `FINAL_DECISION=FREEZE_LOGGING_PIPELINE_AND_PREPARE_FORMAL_PROSPECTIVE_SHADOW_COHORT`
- `Only next task=FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1`

The next task was not executed.

## Further question

The next protocol must decide the formal prospective cohort manifest and analysis denominator before collection, while permanently excluding these pilot rows.
