# Certification–Execution Identity Repair Smoke V1

This directory freezes the future engineering smoke protocol for the repaired certification/execution state identity stack. The protocol-freeze task performs CPU-only validation and does not create the future result root or run GPU/runtime trials.

Future authorized execution order is fixed in `launch_cert_exec_identity_repair_smoke_v1.sh`: verify a clean exact branch and absent root, run CPU static preflight and the protocol validator, create the root, start one tmux session, run one GPU preflight, then run trials 15, 45, and 75 serially in separate processes. The runner stops before any scientific analysis.

`--one` is an internal child mode only. Its authorization is bound to the live parent, exact root, branch, source HEAD, protocol/lock hashes, trial ID, and a secret token hash. Partial or failed evidence is preserved without retry.

The protocol is an engineering integrity check, not a scientific validation. `FAIL_V3_HARD_SAFETY_GATE` remains frozen.
