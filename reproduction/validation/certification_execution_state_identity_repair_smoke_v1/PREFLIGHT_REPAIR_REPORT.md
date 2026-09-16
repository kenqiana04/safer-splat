# Cert-exec identity smoke preflight repair V1

Status: `PASS_CERT_EXEC_IDENTITY_SMOKE_PREFLIGHT_CONFIG_REPAIR_V1`

This retry repaired only the task-local base-config plumbing. The repaired V3
stack now receives the historical V3 protocol as `runtime_base_config`; the
repair-smoke protocol remains separate and unchanged. The original failed
root remains read-only and records a pre-trial GPU-preflight failure with zero
cycles, trials, controller/QP trials, and PlantCommit operations.

CPU validation passed: Python syntax, shell syntax, retry validator, projected
V3 geometry, source/protected-diff checks, and `git diff --check`. One valid
GPU-only preflight then passed after task-local path links exposed the frozen
map/data artifacts; the temporary links were removed. It loaded the frozen
Stonehenge checkpoint and verified the map identity, with zero runtime cycles,
zero PlantCommit, and no scientific analysis. No smoke trial was run.

Frozen runtime geometry remains hard radius `0.015q`, margin `0q`, and
`rho_seg=0q`; historical `0.025q` remains diagnostic-only with no runtime
authority. The frozen scientific decision remains
`FAIL_V3_HARD_SAFETY_GATE`; no scientific result was changed.

Only next task: `MANUALLY_START_FROZEN_CERT_EXEC_IDENTITY_REPAIR_SMOKE_RETRY1`.
