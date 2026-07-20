# TUM Metric Geometry Repair Refinement V1

Result: `BLOCKED_BY_C3_REFINEMENT_BASELINE_NONREPRODUCIBLE`.

All four frozen identities passed: V1R6 checkpoint, config, transforms, and
the 359,140-point metric seed. The initialization wording was corrected:
`random_init=false` does not mean seed initialization when metadata lacks both
3D-point fields; stock Splatfacto therefore takes the random fallback.

The task-owned wrapper preserved the PR #33 C3 dataparser, depth loss (metric
Smooth-L1, lambda 0.10, beta 0.10), seed asset, split, CUDA overlay, and raw
60-frame expected-depth evaluator. Its 100-step smoke passed, with depth loss
and JSONL instrumentation recorded.

The mandatory R0 3k gate did not reproduce the frozen C3 3k result. Frozen C3
was AbsRel 0.333, delta1 0.457, ratio 1.004. The first R0 3k was 0.453/0.364/
1.285; after removing an unnecessary constant-lambda multiplication, the
second was 0.422/0.394/1.234. Both exceed the preregistered tolerances of
0.02/0.03/0.05. R0's independent 1k–6k milestones were retained and evaluated,
but cannot license a refinement-factor conclusion.

Accordingly R1/R2/R3, any candidate selection, a new 10k run, final geometry
gate, formal protocol candidate, static SAFER query, navigation, CBF-QP, G1,
V1R7, and formal training were not executed. The next task must diagnose this
C3 baseline divergence before an ablation is scientifically interpretable.
