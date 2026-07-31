# ARKitScenes SplaTAM canonical-input qualification V1

## Result

`FINAL_STATUS=BLOCKED_BY_ARKITSCENES_SPLATAM_LOADER_OR_METRIC_CONTRACT`

`FINAL_DECISION=STOP_BEFORE_SMOKE_OR_TRAINING_PENDING_LOADER_METRIC_CONTRACT`

The task stopped before smoke and before any mapper execution. No learned Gaussian map was created, exported, evaluated, or published.

## Frozen inputs and authority

- Scene/visit: `48018874` / `483945`.
- Canonical TRAIN: 214 frames, raw Git-blob SHA-256 `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3`, OID `a2ddc70775e6d0f9c25f77ef5f869556d83b292c`, semantic SHA-256 `32adca1e09694dce9ff5bebc895109f32f866e1c8ecc845e3927a07f60129d12`.
- Canonical HELDOUT: 53 frames, raw Git-blob SHA-256 `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7`, OID `cf28dd385711a31733360e5fc21dce229ce605bc`, semantic SHA-256 `69c8328511cd8405b17b2fc17da9f557ed69ac75b3cfc442f380d586ecab7117`.
- Split identity `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`; selected-group tuple `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`.
- Authorities remained fixed: ARKitScenes `7283761bf26c27570ec59a5dc0f8686fbff07726`; SplaTAM `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`; rasterizer source `cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`.

## Source, config, and environment

- The official ScanNet++ RGB-D parent config passed static semantic audit. It keeps camera rotation/translation learning rates at zero and preserves frozen mapping iterations, losses, densification, and pruning.
- The task-owned adapter only accepts the raw canonical TRAIN manifest for scene 48018874. It rejects HELDOUT requests and does not estimate poses, fit scale, run ICP, or use Sim(3).
- The isolated task prefix completed its third allowed environment attempt. The final lock records PyTorch `2.1.2+cu118`, CUDA `11.8`, a task-owned rasterizer compiled from the fixed source, and frozen `natsort`, `kornia`, and `kornia-rs` wheels. Full import of official `scripts.gaussian_splatting` passed.
- The existing reverse-proxy watchdog was restarted once under the user's explicit limited network-recovery authorization after remote loopback proxy refusal. GitHub and PyPI then passed through the existing loopback proxy. No project content was changed by the network repair; see `network_recovery_record.json`.

## Loader/metric gate

Two fresh processes produced the same deterministic audit SHA: `adb90f8ee4fd5638662ae2174e7fd75bd31413639038c987ad33508280fc33b7`.

- Median point-to-mesh distance: 0.01387 m — pass.
- p95: 0.13049 m — pass.
- p99: 0.49156 m — **fail** against the frozen 0.30 m gate.
- 98.44% of sampled frames had per-frame median at most 0.10 m; depth-unit and 2D-to-3D-to-2D checks passed.

The failure is concentrated in valid-positive-depth frames. For example, canonical TRAIN index 78 has 49,152 positive depth pixels but no confidence-2 pixels, and its point-to-mesh median is 0.44440 m. The baseline is frozen to `depth>0`, so replacing those pixels with a confidence mask, removing the frame, or applying pose/scale/ICP correction would violate the protocol.

## Execution boundary

- Smoke: 0; execution lock: 0; formal baseline attempts/completed outputs: 0/0; checkpoint: 0.
- Canonical export, held-out NVS/depth, clearance, SAFER static G0, confidence variant, controller benchmark, and map publish: all 0.
- GPU 1 final state: 6 MiB / 0% and no task-owned compute process.

No automatic next task is authorized. A new explicit protocol is required before changing how the reproducibly inconsistent positive-depth frames are handled.
