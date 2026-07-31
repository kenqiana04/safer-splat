# Frozen SplaTAM source audit

The audited checkout is `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`,
with `diff-gaussian-rasterization-w-depth` at
`cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`.

`scripts/gaussian_splatting.py` is the relevant official offline mapper. It
loads every frame's pose, forms `w2c = inverse(c2w)`, assigns the GT pose to
camera parameters, and sets both camera learning rates to zero in its official
Gaussian-splatting parent configurations. It initialises means from RGB-D,
stores scales in log space, opacities as logits, rotations as WXYZ quaternions,
and uses the depth/silhouette rasterizer for its RGB-D loss.

The iPhone configuration in this frozen checkout targets a different online
entry point and does not supply the offline mapper's `train` contract. The
closest compatible real-RGB-D parent is therefore
`configs/scannetpp/gaussian_splatting.py`; that selection was made before any
runtime operation. No task-owned adapter or configuration was activated,
because the required PR #68 input byte-identity freeze failed first.

No official source file was modified. No environment was created, and no CUDA
code was run.
