# REPORT: TUM C3 3K Reproducibility Divergence Diagnosis V1

## Outcome

`PASS_C3_DIVERGENCE_DIAGNOSED_R0_EXECUTION_DRIFT`

PR #34 base is `e5a61d58ace537494a7f00839b60b1fae306da01`. The diagnostic root is `/disk1/zlab/maintenance_records/tum_c3_3k_repro_divergence_diagnosis_v1`.

## Frozen identities and lineage

- V1R6 checkpoint/config/transforms/metric seed matched all required hashes.
- C3 3k checkpoint: `022e499fc5395d4db674d134fae1801d40d26757c813138b5c904c4c1c5503a1`.
- C3 10k checkpoint: `2664eaac88ddc60a952dd7f6f07d7ac45455f3586dde9066293a8d91d3b9643c`.
- C3 retry2: `FRESH_START_CONFIRMED`.
- Historical asset manifest found 175 readable artifacts and no required evidence gap. The per-run C3 3k config was not persisted; it is canonically reconstructed from the V1R6 config and immutable PR33 launcher.

## Evaluator binding

Historical evaluator A, refinement evaluator B, and independent evaluator C all use fixed 60 frames, raw expected depth, no alignment, and 14,048,828 valid pixels. Frozen C3 3k evaluates to AbsRel 0.3329618806779451, delta1 0.4568739114750355, ratio 1.0041860342025757. This exactly reproduces the archived metric record. C3 10k and both R0 step-3000 checkpoints also reproduce their archived metrics.

## Exact replay result

Replay A and B used only the PR33 Git-object snapshot, seed 20260716, C3 metric seed + depth, 3000 iterations, empty outputs, and no resume. Both exited normally at step 2999.

| Run | AbsRel | delta1 | ratio | vs frozen |
| --- | ---: | ---: | ---: | --- |
| Frozen C3 | 0.332962 | 0.456874 | 1.004186 | reference |
| Exact A | 0.343653 | 0.435374 | 1.005025 | pass |
| Exact B | 0.335564 | 0.439149 | 0.994476 | pass |

Their final Gaussian counts are 340,851 and 345,238 respectively; final tensor hashes differ, but their metrics are within the preregistered tolerance. Initial tensors, RNG states, and camera sequence were not retroactively captured because the immutable launcher was not instrumented; this is noncritical after the exact baseline pass.

## Cause and boundaries

Primary cause is `R0_WRAPPER_SEMANTIC_DRIFT`. PR34 replaces the PR33 model class and adds new loss-path scheduling, CPU scalar extraction, JSONL instrumentation, CUDA/tensor diagnostic reads, and post-backward dispatch. The third differential replay and deterministic-only probe were not required. Historical C3 remains a valid baseline.

No formal training/checkpoint, R1/R2/R3, navigation, SAFER, CBF-QP, or G1 was run. The next task, if separately authorized, is to resume refinement ablation with the frozen exact PR33 C3 launcher.
