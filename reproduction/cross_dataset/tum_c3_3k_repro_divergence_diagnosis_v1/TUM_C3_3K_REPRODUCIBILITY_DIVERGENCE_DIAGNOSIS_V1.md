# TUM C3 3K Reproducibility Divergence Diagnosis V1

Result: `PASS_C3_DIVERGENCE_DIAGNOSED_R0_EXECUTION_DRIFT`.

The four frozen inputs match their required SHA-256 values. C3 retry2 is a confirmed fresh start: the log states that no Nerfstudio checkpoint was loaded and it trained from scratch. The frozen C3 3k checkpoint is `022e499fc5395d4db674d134fae1801d40d26757c813138b5c904c4c1c5503a1`; C3 10k is `2664eaac88ddc60a952dd7f6f07d7ac45455f3586dde9066293a8d91d3b9643c`.

Evaluator A, B, and independently constructed C bind the frozen C3 3k checkpoint to the same 60-frame raw expected-depth metrics: AbsRel 0.3329618806779451, delta1 0.4568739114750355, and median ratio 1.0041860342025757. The same evaluator matrix reproduces the archived C3 10k and R0 retry metrics. Therefore the historical C3 metric record is valid.

Two independent immutable PR33 replays reached step 2999. Replay A was AbsRel 0.3436534337170453, delta1 0.4353742532829073, ratio 1.005024790763855. Replay B was 0.33556363252855326, 0.4391488741979046, and 0.9944759607315063. Both, and their pairwise difference, are within the frozen 0.02/0.03/0.05 tolerance.

PR34 is not an exact C3 baseline wrapper: it substitutes a new model subclass and adds schedule, per-step scalar extraction, instrumentation, CUDA-memory/quantile/gradient reads, JSONL writes, and a different post-backward control path. This source-level execution drift explains why R0 cannot be treated as an exact C3 replay. No third replay was necessary because the protocol permits stopping after exact C3 reproduction plus a conclusive source difference.

No formal training, V1R7, R1/R2/R3, 10k run, navigation, SAFER rollout, CBF-QP, or G1 was executed. A future refinement ablation requires separate authorization and must use the frozen exact PR33 C3 launcher as baseline.
