# Retry2 execution-lock wiring R3

`PASS_CERT_EXEC_IDENTITY_SMOKE_LOCK_POINTER_R3`

The runner's active `LOCK_PATH` now resolves to
`SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY2_R3.json`. The new lock records the
post-code-commit hashes of the runner, launcher, validator, and monitor.
Both earlier attempt roots are preserved by exact file manifests. The launcher
and monitor target the fresh retry2 root, which remains absent.

`gpu_preflight()` now catches failures in identity verification, delegate
loading, and delegate execution. A CPU synthetic hash-mismatch fixture
confirmed that an identity failure produces `gpu_preflight_failure.json`
with zero trial, cycle, controller/QP, and PlantCommit counts. CPU static
preflight, validator, syntax checks, and `--prelaunch-check-only` passed.

No GPU, tmux, smoke, or scientific analysis ran in this task. The frozen
scientific decision remains `FAIL_V3_HARD_SAFETY_GATE`.

Only next task: `HOLD_FOR_INDEPENDENT_MANUAL_RETRY2_LAUNCH_AUDIT`.
