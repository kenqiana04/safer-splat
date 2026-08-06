# REPORT: Resumed Replica GT Executable-Safety Activated Benchmark V1

**FINAL_STATUS:** `PASS_ACTIVATED_MECHANISM_WITH_LOW_REPRESENTATIVE_PREVALENCE`
**FINAL_DECISION:** `DO_NOT_FRAME_CORE_V1_AS_BROAD_REAL_TIME_REPLACEMENT_FOR_SAFER`
**Only next task:** `DECIDE_BETWEEN_FAST_GAUSSIAN_SWEPT_CERTIFICATE_AND_BACKUP_SET_RESEARCH_V1`

> This is configuration-specific evidence on the frozen Replica GT-FINE represented map. It is not a deployment, real-time, collision-superiority, or cross-map generalization claim.

## Answer first

FAS-CBF Core V1 passed the preregistered activated mechanism test: the swept-segment and backup layers produced the intended distinctions, and B3 recovered certified control in all 20 locked G3 states where B2 could not. The represented-map backend produced zero false-safe records. However, the method-independent 160-state representative holdout contained no segment/backup-added rejection and no directional selection. The frozen representative-relevance gate therefore failed, so Core V1 must not be framed as a broad real-time SAFER replacement.

## Frozen lineage and identities

- PR #84: `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`; preserved by frozen identity and artifact manifest.
- PR #85: `7afef38392bec36d9d9811e5a22c816da5faf1ff`; preserved by frozen identity and artifact manifest.
- PR #86: `d4f20f44a810afc2d6379853a286a3e18b175221`; base `7afef38392bec36d9d9811e5a22c816da5faf1ff`; preserved by frozen identity and artifact manifest.
- Certifier identity: `FAS_CBF_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_V1@04ebca2b1b35124ad0e61ebed96e491c9edae4bb:c7928d4032e9da8ad65e39134fd480c6f1828ba2a28ee4c76ac5c7e64c2bdd35`.
- Directional library: `REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1`; SHA-256 `3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe`.
- Map snapshot: `3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55`.
- Reference mesh SHA-256: `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182`.
- Model: `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, dt=0.05, |u|∞≤0.1, |v|∞≤0.1, robot=0.1 m, margin=0.01 m, effective radius=0.11 m, H=20.

## Cohorts and leakage boundary

Activated search evaluated 5744 candidates, all 5744 physical-valid, and stopped after targets were met. Locked G0-G5 counts are {'G0': 20, 'G1': 20, 'G2': 20, 'G3': 20, 'G4': 10, 'G5': 10} under `A1_ALL_TARGETS_MET`.
The representative generator formed 2000 method-independent candidates and locked 160. Registry SHAs are `3f4046eb4d326b3666e7e829f58a01fe84f4a4d3c3c2e09e3336fc8d1b4ef321` and `eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a`; overlap=0. Each registry rebuilt identically in three fresh processes. Pre-lock future-reference reads and formal method runs were both zero.

## One-step paired results

| Method | Cohort | n | Commit | Directional | Terminal | Fail-closed | Deadline miss | Mean progress (m) | Mean runtime (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | ACTIVATED | 100 | 90 | 0 | 0 | 10 | 0 | 0.000469 | 0.006735 |
| B0 | REPRESENTATIVE_HOLDOUT | 160 | 160 | 0 | 0 | 0 | 0 | 0.002484 | 0.001876 |
| B1 | ACTIVATED | 100 | 70 | 0 | 0 | 30 | 0 | 0.000762 | 0.009510 |
| B1 | REPRESENTATIVE_HOLDOUT | 160 | 160 | 0 | 0 | 0 | 0 | 0.002484 | 0.005029 |
| B2 | ACTIVATED | 100 | 30 | 0 | 10 | 70 | 17 | 0.000029 | 0.029378 |
| B2 | REPRESENTATIVE_HOLDOUT | 160 | 160 | 0 | 35 | 0 | 63 | 0.002484 | 0.044820 |
| B3 | ACTIVATED | 100 | 50 | 20 | 10 | 50 | 45 | 0.000508 | 0.047496 |
| B3 | REPRESENTATIVE_HOLDOUT | 160 | 160 | 0 | 35 | 0 | 71 | 0.002484 | 0.046619 |

### Mechanism attribution

- G1: B0 committed 20/20 while B1 rejected 20/20 by the swept-segment layer.
- G2/G3: B1 committed 40/40 while B2 rejected 40/40 after terminal/backup certification.
- G3: B3 selected a frozen directional slot and committed 20/20; B2 committed 0/20.
- G3 bounded rollout: positive progress in 20/20 B3 episodes; reference collisions=0.
- G0: B0 and B3 both committed 20/20 with identical one-step progress; no G0 over-rejection was observed.

## Representative prevalence and utility

- Segment activation: 0/160 (0.00%; Wilson 95% CI 0.00%–2.34%).
- Backup activation: 0/160 (0.00%).
- Directional selection: 0/160 (0.00%).
- B3 fail-closed: 0/160; terminal action: 35/160.
- B3 representative bounded-rollout mean progress: 0.013524 m; reference-safe-but-rejected: 0/160.

The representative relevance threshold (at least eight segment/backup-added states or four directional selections) was not met. Activated group frequencies are deliberately not used as prevalence estimates.

## Represented-map and offline-reference evidence

- Represented false-safe count: 0 across one-step and rollout.
- Offline immediate reference collisions after committed controls: 0; rollout collisions: 0.
- Map-reference disagreement: 30 unique states (120 method-records). These are map-vs-mesh differences, not certifier implementation errors.
- With zero B0/B3 collision events, no reference collision-superiority claim is made.

## Runtime and realism

Across 1040 one-step method records, deadline misses=196. B3 miss rate=44.62%. Semantic certification and the 50 ms diagnostic are reported separately; the benchmark does not establish real-time readiness.

## Preregistered H1-H7

| H | Contrast | Raw p | Holm p | Result |
|---|---|---:|---:|---|
| H1 | G1 segment-based noncommit | 1.907e-06 | 7.629e-06 | SUPPORTED_MECHANISM_EXISTENCE |
| H2 | G2/G3 backup discrimination | 1.819e-12 | 9.095e-12 | SUPPORTED_BACKUP_DISCRIMINATION |
| H3 | G3 certified-control directional rescue | 1.907e-06 | 7.629e-06 | SUPPORTED_DIRECTIONAL_RESCUE |
| H4 | G0 commit preservation | 1 | 1 | NO_G0_COMMIT_OR_PROGRESS_PENALTY_OBSERVED |
| H5 | representative prevalence | N/A | N/A | LOW_REPRESENTATIVE_GATE_AND_RESCUE_PREVALENCE |
| H6 | offline reference collision after commit | 1 | 1 | NO_REFERENCE_COLLISION_EVENTS_NO_SUPERIORITY_CLAIM |
| H7 | 50ms deadline miss | 2.407e-35 | 1.444e-34 | RUNTIME_DIAGNOSTIC_RECORDED_NOT_REALTIME_CLAIM |

H5 is descriptive because no post-hoc null threshold was introduced. H6 has no collision events and therefore supports no superiority inference. Holm correction covers the evaluable inferential contrasts.

## Project decision gates

- Scientific mechanism gate: **True**.
- Active utility gate: **True**.
- Representative relevance gate: **False**.
- No adverse reference regression: **True**.
- Frozen decision-tree case: **C**.

## Claim boundary

- Supported: ACTIVATED cohort establishes configuration-specific segment and backup gate existence.
- Supported: ACTIVATED G3 establishes configuration-specific B3 directional rescue over B2.
- Supported: The represented-map backend produced zero represented false-safe records.
- Not supported: Activated cohort prevalence or natural frequency.
- Not supported: Broad representative relevance for segment, backup, or directional rescue.
- Not supported: Reference collision superiority because no B0/B3 collision events occurred.
- Not supported: Real-time or deployment readiness.
- Not supported: Generalization beyond the frozen Replica GT-FINE configuration.

## Execution and operational audit

Formal attempt count=1; infrastructure failures=1; same-manifest resumes=1. The interruption occurred before any completed formal output, and no scientific result was replaced.
Map training/mutation=0/0; dataset switches=0; parameter/safety-threshold tuning=0/0; protected-source mutation=0. Operational autonomy actions=6.
GPU 1 final compute processes=0 at 6 MiB / 0%; reverse proxy listener preserved=True; watchdog state=Running.
Validator status: `PASS_RESUMED_REPLICA_GT_EXECUTABLE_SAFETY_BENCHMARK_VALIDATION`.

## Evidence locations

- Server task root: `/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1`
- Report: `report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`
- Downstream handoff: `report/downstream_handoff.json`
- Figures: `figures/` (32 preregistered PNGs)

## Final disposition

`FINAL_STATUS=PASS_ACTIVATED_MECHANISM_WITH_LOW_REPRESENTATIVE_PREVALENCE`

`FINAL_DECISION=DO_NOT_FRAME_CORE_V1_AS_BROAD_REAL_TIME_REPLACEMENT_FOR_SAFER`

`ONLY_NEXT_TASK=DECIDE_BETWEEN_FAST_GAUSSIAN_SWEPT_CERTIFICATE_AND_BACKUP_SET_RESEARCH_V1`
