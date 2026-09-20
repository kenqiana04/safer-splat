# Repair and start Formal85 execution harness R2

- Base: `bc96a745af658aa2c8df404fba403dbed4c7b7fe`.
- Attempt0, Retry1, and Retry2 remain immutable zero-cycle, zero-PlantCommit harness failures.
- Retry1 root cause: `FORMAL85_RETRY1_CHILD_RUNTIME_VALIDATOR_PHASE_MISMATCH`.
- Replaces the boolean validator shim with explicit FREEZE, PRELAUNCH, BATCH_RUNTIME, CHILD_RUNTIME, and POSTCOLLECTION contracts.
- Both child startup and delegated source/map verification use CHILD_RUNTIME validation; active task tmux is expected rather than rejected.
- Retry3 has a new root, tmux, launch marker, and R3 authorization token after correcting the partial-raw versus immutable-evidence distinction exposed by Retry2.
- Exact formal85 cohort, Reference, map, geometry, dynamics, Recovery, NI, and boundary semantics are unchanged; scientific diff count is zero.
- Protected runtime diff is zero. Analyzer remains postcollection-only.
- Launch occurs only from a clean pushed commit after CPU/static/integration and final prelaunch PASS.
