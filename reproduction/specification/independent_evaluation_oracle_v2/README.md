# Independent Evaluation Oracle V2

Design-only, posthoc/read-only freeze based exactly on PR #113 head `5595e56b756291881fb9f6f17ba3d7551263574f`. It separates method-internal diagnostics, execution-trace facts, represented-map-relative outcomes, and scene-scoped external ground truth. It defines immutable trace, swept-segment collision/margin outcomes, goal/progress, role accounting, UNKNOWN, paired trial aggregation, anti-circularity checks, and claim boundaries.

No runtime or oracle evaluator is implemented. No controller, map, dynamics, dataset, trial, GPU, rollout, benchmark, or formal collection is changed or executed.
