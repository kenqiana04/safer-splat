# TUM Exact Functional-Autograd Ellipsoid Solver Parity V1

## Result

`FUNCTIONAL_GRADIENT_PARITY_FAILED`

This task is a solver-equivalence audit, not map training or map modification. PR #40 was open Draft at `babc37d800ab461dc11bf880ecbdf0db43c8ad69`; its adapter and native-render evidence remains valid.

## Frozen source and recovered failure

The frozen PR #40 blobs are `splat/distances.py` `81940ca59297a2ee3b4214901b038725c2748318` and `splat/gsplat_utils.py` `4e704349ddb5b5d6737e38d63965699ecfe81030`. The actual failed server script was recovered byte-for-byte from `/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/functional_autograd_gate.py`.

The official root solver uses a two-column bound table, then `torch.mean(s, dim=-1, keepdims=True)` before each of 25 source-order updates. It uses `sorted_scales + 1e-8` only for the distance solver and unperturbed sorted scales for phi.

## First divergence and forward repair

The first divergence was iteration 0 midpoint evaluation. The old functional implementation used `(lower + upper).mul(0.5)`; the official uses `torch.mean` over contiguous two-column bounds. The exact functional implementation now uses `torch.stack((lower, upper), dim=-1)`, `torch.mean`, and non-inplace `torch.where` updates. It has no in-place bound updates and retains a real PyTorch autograd graph.

On 4,096 fixed CUDA float32 synthetic cases, returned midpoint, yhat, and squared distance are bitwise exact, with h maximum absolute difference `0.0`.

## Blocking gradient result

Although the repaired forward is exact, reverse-mode autograd through the finite 25-iteration bisection does not satisfy the frozen official analytical-gradient parity gate. The discrepancy is a gradient-contract issue, not a map, adapter, coordinate, scale, renderer, or forward-solver issue. Custom backward, threshold relaxation, float64 substitution, and full 908 reruns are prohibited by protocol.

Therefore no full-908 functional audit, static SAFER rerun, or G0 classification was run. No negative h point was removed. h remains a repository ellipsoid safety value, not metre clearance.

No controller, dynamics, QP, trajectory, navigation, SAFER rollout, G1, formal training, or V1R7 was executed.

## Recommended next task

`SAFER Ellipsoid Solver Numerical Contract Calibration V1` requires separate authorization. It must resolve whether the frozen analytical gradient or finite-iteration differentiable forward graph is the applicable static contract before any G0 or G1 work.
