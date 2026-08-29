# Validate L2/H1 shadow instrumentation OFF-vs-ON equivalence V1

## Technical summary

**Result: PASS, CASE_A.** The preregistered bounded Stonehenge QA executed 21 real navigation runs: six fresh-process self-consistency runs plus five frozen trial IDs across NATIVE_OFF, WRAPPER_OFF, and WRAPPER_ON. All 21 exact comparisons passed; no first divergence was found. The active C arm produced 1490 immutable captures and 1490 joinable certificate results with zero controller intervention, zero candidate replacement, and no leftover shadow worker.

This supports only a bounded runtime non-interference claim under the tested deterministic conditions. It is not a collision/progress experiment, a logging-completeness pilot, a runtime benchmark, or a formal prospective cohort.

## Direct answers to the 25 required questions

1. **Q1 — PR #97 exact identity?** YES. Expected and actual head: `7d48bf6c3b8932aa65d851c3cd70404404453cb3`; PR #97 was frozen as Open Draft before navigation.
2. **Q2 — Trial IDs frozen before results?** YES. Stable sorted official100 rows with positions `floor(j*(N-1)/(K-1))`, `N=100`, `K=5`, yielded `[0, 24, 49, 74, 99]` before any QA navigation.
3. **Q3 — A/B/C used?** YES: NATIVE_OFF, WRAPPER_OFF, WRAPPER_ON.
4. **Q4 — A truly had no wrapper?** YES. Seven A activations report `wrapper_loaded=false`, observer off, no worker.
5. **Q5 — B wrapper loaded but observer disabled?** YES. Seven B activations report real wrapper delegation, observer off, and no worker start.
6. **Q6 — C fully active?** YES. Seven C activations report wrapper, immutable capture, bounded queue, worker, frozen L0/L1/L2, append-only logs, and complete shutdown.
7. **Q7 — A self-consistency?** PASS; A1=A2 exactly, 318 steps.
8. **Q8 — B self-consistency?** PASS; B1=B2 exactly, 318 steps.
9. **Q9 — C self-consistency?** PASS; C1=C2 exactly, 318 steps; both processed 318 observations.
10. **Q10 — A vs B selected-u exact?** YES for all five frozen trials.
11. **Q11 — B vs C selected-u exact?** YES for all five frozen trials.
12. **Q12 — A vs C selected-u exact?** YES for all five frozen trials.
13. **Q13 — State trace exact?** YES, via the canonical per-step comparator.
14. **Q14 — Solver/branch exact?** YES.
15. **Q15 — Plant input/output exact?** YES.
16. **Q16 — Termination exact?** YES.
17. **Q17 — First divergence?** NONE; `first_divergence_count=0`.
18. **Q18 — Tolerance modified after results?** NO. Equality remained exact; floats were canonicalized with `float.hex()` and `numeric_tolerance=null`.
19. **Q19 — Trial replaced based on L2 result?** NO; candidate/trial replacement count is zero.
20. **Q20 — C logs parse and join?** YES for all seven C runs; payload hashes join and selected `u_k` is present.
21. **Q21 — Treated as logging pilot?** NO; `logging_pilot_run_count=0`.
22. **Q22 — Collision/progress treated as performance?** NO; they appear only inside trace identity QA.
23. **Q23 — Formal 100-trial prospective cohort run?** NO; `formal_on_policy_cohort_count=0`.
24. **Q24 — Maximum claim?** No observed control-trace perturbation across the preregistered bounded five-trial Stonehenge manifest under the tested deterministic conditions.
25. **Q25 — Next step?** `VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1`, only after separate authorization.

## Five frozen trials all matched exactly

| Trial | Steps | Canonical trace SHA-256 | A=B=C | C captures/results |
|---:|---:|---|:---:|---:|
| 0 | 318 | `ef4b6437b3496c9a422ef1c0e02780747457cba269b99e63f962c291e1f9559a` | YES | 318/318 |
| 24 | 148 | `0e02c147eae2b5a082e133dcefb8865da4c7358abdffc37ad24e5d400169af9e` | YES | 148/148 |
| 49 | 43 | `252b50ecba6fc0cd77a470ab4dca9b7e0ccdf8b0d9e5678a1a3b20fea70ec260` | YES | 43/43 |
| 74 | 27 | `b3ceb2b293e478f04dad59c82810618767fcf8f99703435a26b78e35e0af12f3` | YES | 27/27 |
| 99 | 318 | `d5faa05402b8a1f73bcb8f58e9bcb9ed2b5c7e3477df83b337e7b40dac34792c` | YES | 318/318 |

The table is used instead of a chart because the scientific question is exact identity, not magnitude or trend. A visual encoding would add no information beyond the per-trial hashes and exact flags.

## Scope, cohort, and equality contract

The QA cohort is five deterministic Stonehenge trial IDs selected before results. Each trial ran in three fresh processes using the same seed, GPU, official environment, map authority, protected `run.py`, and frozen controller. The primary trace includes aligned state, nominal command, selected command, solver/branch, plant input/output, termination, goal, and map identity fields. Equality is byte-stable semantic equality after deterministic JSON normalization and exact hexadecimal float representation; no numerical tolerance is permitted.

## The three-arm method isolated wrapper and observer effects

- **A — NATIVE_OFF:** protected run without importing the PR #97 wrapper.
- **B — WRAPPER_OFF:** exact PR #97 wrapper with real delegation, observer disabled, and no worker.
- **C — WRAPPER_ON:** the same wrapper with immutable observation copy, bounded nonblocking queue, real worker, frozen L0/L1/L2 evaluation, and append-only logs.

The self-consistency gate passed separately for A, B, and C before the five-trial matrix. A-versus-B isolates wrapper loading; B-versus-C isolates active shadow observation; A-versus-C tests the end-to-end difference.

## Arm C was active but had zero authority

Across seven C runs, capture, certificate-result, and worker-processed totals were all 1490. All C activations completed shutdown, reported no leftover worker, and retained `controller_authority=false`. Queue/worker evidence was inspected only for minimal parse/join sanity. It does not estimate logging completeness or runtime suitability.

## Robustness and failure handling

The first launch attempt stopped before map construction because the task-local isolated run directory mapped `outputs` but omitted the frozen config's relative `data` path. It produced zero control steps. The failed directory and traceback were retained; the task-local wrapper was corrected to add a read-only `data` symlink, and the full matrix restarted from a clean output root. No protected source, controller, instrumentation implementation, map, trial, seed, threshold, or result was changed.

Independent checks found one environment identity and one map authority identity across all 21 valid runs. The protected raw-Git audit matched all 17 blobs with zero protected-path diff.

## Limitations and bounded interpretation

The manifest contains five Stonehenge trials, not the official100 cohort. Exact equality here does not prove equivalence for untested trials, other maps, nondeterministic environments, or future code. It also does not show collision reduction, progress improvement, intervention efficacy, real-time feasibility, deployment safety, or logging completeness. Shadow results never had decision authority, so this task cannot measure control benefit.

## Recommended next step

Freeze this bounded non-interference evidence. If separately authorized, run `VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1` with its own pre-frozen manifest and completeness gates. Do not infer or execute that task automatically from this PASS.

## Further questions

- Will a separately preregistered pilot meet required `u_k`, reachability, map-authority, queue/drop, and join completeness gates?
- Does instrumentation remain non-interfering under any future environment or controller change? Such a change requires a new equivalence qualification.

## Final decision

- `FINAL_STATUS=PASS_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1`
- `FINAL_DECISION=FREEZE_RUNTIME_NONINTERFERENCE_EVIDENCE_AND_VALIDATE_LOGGING_COMPLETENESS_PILOT`
- `Only_next_task=VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1`
