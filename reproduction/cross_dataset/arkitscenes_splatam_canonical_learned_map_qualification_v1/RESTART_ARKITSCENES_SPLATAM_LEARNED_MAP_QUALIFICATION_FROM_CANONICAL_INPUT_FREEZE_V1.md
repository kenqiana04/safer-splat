# ARKitScenes canonical-input SplaTAM learned-map qualification

This task consumes only the PR #70 canonical Git-blob mapping inputs for scene 48018874. It freezes the source, configuration, environment, guarded TRAIN-only adapter, evaluator registries, smoke, execution lock, one baseline, and at most one conditional confidence-mask variant. It does not run a controller or planner benchmark.

The raw-byte authority for both manifests is `SHA-256(git cat-file blob <commit>:<path>)`; semantic CSV identities are a secondary equality check. PR #68, #69, and #70 remain immutable lineage evidence.
