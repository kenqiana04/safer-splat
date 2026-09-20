# Repair Formal85 Attempt0 execution-lock path mismatch R1

- Exact repair base: `6f6ac91be5ffa4ad7c0b8ed3d3851f3293c4979b`.
- Attempt0 remains immutable and stopped before runtime startup, public cycles, Recovery evaluation, or PlantCommit.
- Root cause: `FORMAL85_ATTEMPT0_EXECUTION_HARNESS_LOCK_PATH_MISMATCH`.
- Minimal repair: the child runner now binds the same canonical lock basename as validator and launcher.
- No duplicate or wrong-basename lock was created.
- Retry1 uses a new result root, tmux session, launch marker, and authorization token.
- Validator now checks structured runner/launcher binding, uniqueness, wrong-name absence, synthetic hash-path access, token consistency, and Attempt0 hashes.
- Exact formal85 order, immutable Reference, map, geometry, dynamics, Recovery, hard-safety gate, progress NI, statistics, and boundary semantics are unchanged.
- Scientific semantic diff count: `0`.
- GPU/tmux/real-trial/real-PlantCommit counts: `0/0/0/0`.
- Historical repaired-Active verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`; Retry1 is `NOT_RUN`.
- Only next task: `EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_RETRY1_V1`.
