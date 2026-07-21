# TUM Dedicated RGB-D Gaussian Baseline Comparison V1

## Result

`PASS_TUM_DEDICATED_RGBD_BASELINE_DEGRADED_SUPERIOR`

Both dedicated RGB-D Gaussian mapping baselines completed a fresh 240-frame
map construction from the frozen TUM `freiburg1_room` train set and a native,
raw-scale 60-frame held-out evaluation.  SplaTAM is the best external method
on the fixed evaluation; both external methods exceed the unchanged numerical
`delta1 >= 0.75` threshold.  This is **not** a G0 pass: no jointly verified
common Gaussian adapter exists, so static SAFER/G0 is deliberately not run.

## Frozen inputs and methods

- Transform SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.
- Split: 240 train / 60 held-out evaluation, disjoint and exhaustive; full
  registry SHA-256: `b06fc045fe7fd145f1590afaff8e1f0a92fcce7513c3316a14c1ed3927b770c8`.
- Metric depth scale: `0.0002`; intrinsics: `fx=517.3`, `fy=516.5`,
  `cx=318.6`, `cy=255.3`, `640x480`.
- SplaTAM official archive commit `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
  (`https://github.com/spla-tam/SplaTAM.git`), including fixed depth-rasterizer
  submodule `cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`.
- Gaussian-SLAM official archive commit `eaec10d73ce7511563882b8856896e06d1f804e3`
  (`https://github.com/VladimirYugay/Gaussian-SLAM.git`).
- Both are `MAP_ONLY_COMPARABLE`: the release GT-pose path is used and source
  audit records zero mapping-core changes. Tracking performance is excluded.

## Protocol

Every held-out metric below is computed at native metric scale with no scale
fitting, Sim(3), or per-frame alignment.  The first evaluation frame is an
anchor needed only because the official TUM loader rebases its first pose; it
is strictly excluded, leaving exactly 60 scored frames.  Depth range bins are
fixed at near `[0,1) m`, mid `[1,3) m`, and far `[3,+inf) m`.

SplaTAM uses its official CUDA rasterizer; depth is the alpha-composited
expected camera-z value from its official depth-plus-silhouette path.
Gaussian-SLAM uses its official native `render_gaussian_model`.  Its release
loop persists completed submaps; the task-owned launcher only exports the
otherwise-live final submap after mapping, then native evaluation concatenates
those already-global-coordinate Gaussian tensors without a parameter update.

## Primary metric comparison

| Method | AbsRel | RMSE (m) | delta1 | delta2 | delta3 | PSNR | MS-SSIM | LPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Internal tuned C_L050_K2000_B020 | 0.188127 | 0.477082 | 0.685632 | — | — | — | — | — |
| Internal S2 point-to-plane | 0.197457 | 0.499080 | 0.671166 | — | — | — | — | — |
| SplaTAM GT-pose map-only | **0.027134** | **0.136266** | **0.979695** | **0.991436** | **0.996478** | **19.1909** | **0.7797** | **0.3298** |
| Gaussian-SLAM GT-pose map-only | 0.065761 | 0.241765 | 0.939383 | 0.972758 | 0.986355 | 14.8630 | 0.5667 | 0.4565 |

SplaTAM near/mid/far `delta1`: `0.963731 / 0.978166 / 0.876260`.
Gaussian-SLAM near/mid/far `delta1`: `0.960614 / 0.928576 / 0.717181`.
The Gaussian-SLAM far-range degradation is a result observation, not an
adapter, SAFER, controller, navigation, or G1 conclusion.

## Execution evidence

- Server/GPU: physical GPU 1, RTX 4090 UUID
  `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`, driver `525.147.05`.
- SplaTAM: the already-frozen 30K map completed once; params SHA-256
  `cb4a8f133a4ce4063f60112fa9689db683988be29f67b9d570231a319849a36f`.
- Gaussian-SLAM: 5-frame and 30-frame smoke passed; one fresh 240-frame map
  then completed with 240 mapping visualizations and 25 submap checkpoints.
- Gaussian-SLAM runtime: PyTorch `2.1.2`, CUDA `12.1`, FAISS GPU `1.8.0` in a
  task-owned Conda environment. Earlier venv-only attempts were not used for
  results because PyPI FAISS wheels had CUDA/ELF ABI failures.
- Final validator: all seven checks passed, including split integrity,
  map-only protocol, both native evaluations, adapter fail-closed behavior,
  static-not-run behavior, and the no-execution boundary.

## Boundaries and next step

`COMMON_ADAPTER_UNRESOLVED` is intentional. The two releases have not yet
provided a jointly executable proof of coordinate semantics, parameter
semantics, renderer assumptions, scale handling, and normal conventions for
the project common Gaussian loader. Therefore no common expected-depth,
frozen-908, gradient, continuity, static SAFER, controller, dynamics, QP,
trajectory, navigation, G0, or G1 task ran. No formal Splatfacto training was
started.

The only recommended follow-up is a separately authorized **TUM Common
Gaussian Map Adapter Qualification V1**. It must establish that semantic proof
before any static SAFER/G0 audit; this task does not start it automatically.
