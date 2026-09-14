# Freeze Active Runtime V3 Paired Scientific Validation Protocol

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION_PROTOCOL_FREEZE`

`FINAL_DECISION=READY_TO_EXECUTE_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION`

`ONLY_NEXT_TASK=EXECUTE_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_VALIDATION`

## Scientific role

This protocol freezes `REPEATED_BENCHMARK_PAIRED_VALIDATION_V3` on the Stonehenge benchmark. Formal V2 outcomes were exposed before V3 was formed, so the 85 trials are explicitly labeled `OUTCOME_EXPOSED_REPEATED_BENCHMARK_VALIDATION`, not a pristine untouched confirmatory holdout. The future result may support bounded statements about the frozen benchmark only; it cannot establish map-independent, population-level, physical-world, hard real-time, or deployment validity.

Pilot V3 supplied runtime and evidence-integrity support: 10/10 trials completed with finalization and trace cardinality PASS, zero selected/executed mismatch, zero nonfinite values, zero actuator violations, zero incomplete/recovery/plant-unknown events, observed runtime radius only `0.015 q`, and zero historical-shell intrusion/authority events. Pilot evidence is not an efficacy result.

## Cohort and future execution

The future Active V3 execution contains exactly the Formal V2 `PRIMARY_FORMAL_85`, in the frozen Formal V2 execution order after removing the 15 development-exposed IDs. The 15 development trials are neither scheduled nor added as a secondary GPU cohort. Execution is frozen as serial, one process per Active arm, seed 0, at most 500 completed cycles, GPU 1, and `/disk1/zlab/conda_envs/safer_splat_official`.

## Immutable Reference reuse

Reference comparison is mandatory, but Reference rerun is forbidden. `V3_REFERENCE_REUSE_LOCK.json` independently resolved 85/85 accepted `REFERENCE_CBF_QP` arms from `/disk1/zlab/formal_execution_records/formal_paired_v2_20260911`. Every entry records the Formal V2 source identity, map/checkpoint, start/goal, seed, dynamics/controller contract, accepted summary hash, raw-evidence-lock identity and hash, trajectory/action evidence hash, typed termination, oracle-input availability, and eligibility/finalization proof. All recorded raw component hashes were recomputed against the immutable evidence tree.

## Frozen scientific gates

The integrity gate requires exactly 85 eligible pairs and zero runtime/evidence violations. The primary hard-safety gate uses only `r_hard=0.015 q`, `m_hard=0 q`, and `rho_seg=0 q`, requiring zero Active swept-segment violations, zero Active collision-proxy trials, zero Active-only hard-collision discordances, and zero unresolved oracle UNKNOWNs. The historical `0.025 q` shell is diagnostic-only and has no primary, eligibility, runtime, routing, fallback, arbitration, or ranking authority.

The progress gate uses un-clipped normalized progress `(d_start-d_final)/d_start`. The primary estimand is mean paired `Active V3 - reused Reference` progress over all 85 pairs. The fixed noninferiority margin is `-0.02`; use 10,000 pair-bootstrap resamples, seed `20260911`, and a 95% percentile interval. PASS requires the lower bound to be strictly greater than `-0.02`.

## Execution boundary

This protocol-freeze task executed zero Active V3 arms, zero Reference reruns, zero scientific oracle jobs, zero Official100 jobs, and zero new Formal outcomes. No shared runtime, controller, CBF, dynamics, map, checkpoint, certificate, Pilot, Smoke, or Formal artifact was modified. The next task may execute only the frozen protocol; any scientific/runtime semantic change requires a new protocol version.
