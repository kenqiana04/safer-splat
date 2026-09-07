# Execute Refrozen BYPASS Equivalence V2R1

## Answer first

`ACTIVE_HARNESS_BYPASS` was completely transparent to the frozen Stonehenge reference control/plant behavior under the V2R1 QA contract. All five fresh pairs passed exact comparison. Across 732 joined cycles, reference-to-supplied actions, supplied/selected/executed actions, post-states, solver/branch values, and termination reason/step were exact; every mismatch count was zero.

`FINAL_STATUS=PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1`

`FINAL_DECISION=FREEZE_BYPASS_EQUIVALENCE_AND_ADVANCE_VALIDATION_LADDER`

## Frozen authority

- PR #118: Open Draft, head `a537ff653ac896aa1ab567b5197136efa1a937b4`, base `06833d2bcf9649c0912133b8a28b1a0c4ec6f4f8`.
- Protocol raw SHA-256: `f0206a54551d9fc93ef6a5e5c6a6dbf71c043c7882d0c34030180ca215161c52`.
- Input lock SHA-256: `d9309a93790567e972d7c27a01577838a02aab2e549558d97e022e48a4adad8d`.
- Execution lock SHA-256: `7403a0fdb54d6f25e1e1aa3ba4f40b799e78257c77e3d3cc34e54af7d1e8df76`.
- Source freeze SHA-256: `0760bdde263188d80b75379dd7eb4f48feb3124b6d51b90a5c88e16d61962f9c`.
- Environment: Python 3.10.20; PyTorch 2.1.2+cu118; CUDA 11.8; NumPy 1.26.4; Clarabel 0.10.0; physical GPU 1, NVIDIA GeForce RTX 4090.
- Stonehenge config/dataparser/checkpoint identities matched the input lock.
- Q0R1: 12/12 PASS.

## Execution

| Trial | Canonical ID | Compared steps | Termination | Result |
|---:|---|---:|---|---|
| 50 | `STONEHENGE_TRIAL_050` | 40 | `NOT_MOVING` at 39 | PASS |
| 10 | `STONEHENGE_TRIAL_010` | 255 | `NOT_MOVING` at 254 | PASS |
| 30 | `STONEHENGE_TRIAL_030` | 43 | `NOT_MOVING` at 42 | PASS |
| 70 | `STONEHENGE_TRIAL_070` | 152 | `NOT_MOVING` at 151 | PASS |
| 90 | `STONEHENGE_TRIAL_090` | 242 | `NOT_MOVING` at 241 | PASS |

The sentinel pair ran first and passed before the remaining four pairs. The final real-arm counter was 10/10. Source correction quota after the first real arm remained 0. Five BYPASS finalized trace locks were present. Intervention, token mutation, and protocol-deviation counts were all zero. GPU 1 had no task-owned compute process after completion.

## Infrastructure-only precursor

Before the real sequence, one invocation stopped before map loading completed because the new task checkout did not expose the existing `data/stonehenge/transforms.json` path. It had zero solver steps, zero plant commits, zero finalized traces, and zero comparison evidence. It was therefore recorded as `PATH_LINK_ENV_PACKAGING_ONLY` and did not consume the real-arm counter. The frozen dataset directory was linked into the task checkout; no source, protocol, lock, parameter, or asset content changed. The failed invocation and ledger remain preserved under `infrastructure_only_attempt_01/`.

## Validation and claim boundary

The final validator passed 26/26 checks with verdict `PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1_VALIDATION`. The independent compact reviewer verdict was `PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1`.

This result proves only V2R1 QA noninterference. It does not prove ACTIVE V2 safety, collision reduction, control efficacy, performance improvement, zero overhead, real-time behavior, or deployment safety. ACTIVE mode, scientific oracle evaluation, official100, and smoke were not executed.

Remaining blocker: ACTIVE runtime contract conformance is not yet validated.

Only next task: `VALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2`. It is not authorized or executed by this task.
