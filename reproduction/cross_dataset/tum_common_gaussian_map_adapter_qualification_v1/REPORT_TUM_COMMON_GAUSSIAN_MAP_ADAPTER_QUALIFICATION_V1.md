# TUM Common Gaussian Map Adapter Qualification V1

## Result

`TUM_COMMON_ADAPTER_VERIFIED_STATIC_SAFER_INVALID_STOP`

PR #39 was open and Draft at frozen head `e7d27e9ffa9e2314c38c62fee5a612ef6bac5a0c`. This task created no training, mapping, checkpoint, controller, dynamics, QP, trajectory, navigation, SAFER rollout, G1, formal output, or V1R7.

Native depth is not a G0 result: it validates the method renderer under the fixed 240/60 protocol, while G0 additionally requires a fully exact static SAFER functional-autograd path.

## Identity and canonical adapters

- SplaTAM source: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`, source manifest `b54a69791e03b065553b5f4dd75dd6616cfa62e9f3d1bc7d6528b00116c9f13d`; frozen `params.npz` SHA-256 `cb4a8f133a4ce4063f60112fa9689db683988be29f67b9d570231a319849a36f`.
- Gaussian-SLAM source: `eaec10d73ce7511563882b8856896e06d1f804e3`, source manifest `cc6665f3e36b47e80cde84bdb41514b81f96e667cfaae688f5b45c0bcadbebcd`; 25 frozen submaps in the native evaluator concat order, totaling 3,045,467 Gaussians.
- Transforms SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`; frame-registry semantic SHA-256: `b06fc045fe7fd145f1590afaff8e1f0a92fcce7513c3316a14c1ed3927b770c8`; frozen 908-point SHA-256: `5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2`.
- SplaTAM export has 5,464,102 Gaussians. Its means are world coordinates; `log_scales` are exp-activated and isotropically expanded by the official renderer; `unnorm_rotations` are normalized wxyz; `logit_opacities` are sigmoid-activated.
- Gaussian-SLAM uses frozen native-concat global xyz; scaling is exp-activated, rotation is normalized wxyz, opacity is sigmoid-activated, and SH tensors are preserved in canonical shards.
- Both exports were generated twice and byte-identical. No Gaussian was filtered, culled, merged, downsampled, transformed, or altered. Covariance is `R @ diag(scales_linear_m**2) @ R.T` and the sampled positive-definiteness audits passed.

## Renderer and static evidence

Both methods passed native render parity over four train plus eight eval frames. SplaTAM maxima were below `1e-6`; Gaussian-SLAM maxima were below `7e-6`, with exact valid-depth and alpha masks.

Both full maps passed three exact 908-point `GSplatLoader.query_distance(ball-to-ellipsoid, radius=0)` runs: all values and analytical gradients were finite, repetitions and active indices were exact, and all 299 ordered camera-pair continuity differences were within 0.1. Negative h values were retained. h is the repository ellipsoid safety value, not metres of free clearance.

The non-inplace functional-autograd reconstruction was finite for 908/908 points, but its maximum h difference from the official in-place solver was `2.288818359375e-05` for SplaTAM and `7.62939453125e-06` for Gaussian-SLAM. The inherited strict contract requires zero difference. Therefore static SAFER is invalid and G0 is not classified despite the successful native metrics and adapter/render parity.

## Limitations and next action

The remaining critical issue is an exact, source-equivalent functional-autograd solver parity proof. It requires separate authorization. G1 smoke, controller, dynamics, QP, navigation, SAFER rollout, formal training, and V1R7 remain prohibited.
