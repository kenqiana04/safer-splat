# SAFER World-Frame Stable Ellipsoid Hessian Runtime Correction V1

Result: `PASS_SAFER_WORLD_FRAME_STABLE_HESSIAN_RUNTIME_CORRECTION_BOTH_EXTERNAL_G0_ACCEPTABLE`.

Base was PR #43 head `5342992cbf5c46b4b04d0c68ca80ae3c6f40f67e`. The prior task qualified the defect but deliberately did not alter runtime source. This task applied the two qualified corrections only: stable `lambda / (lambda + s**2)` diagonal evaluation in `splat/distances.py`, and signed-local reflection plus `R H R.T` world-frame conversion in `splat/gsplat_utils.py`.

The sign contract selected `RFR`, not `RF0`: `SIGN_REFLECTION_REQUIRED_AND_VERIFIED`. On 4096 CUDA runtime cases, h, analytic gradient, closest point, and active index remained bitwise exact. The independent float64 world-Hessian comparison gave median/p99/max relative error `4.74e-8 / 9.42e-8 / 2.99e-7`; HVP p99/max were `9.77e-8 / 3.29e-7`; all six zero-component cases were finite. The fixed-tensor world-frame CBF algebra smoke passed without importing or running CBF, dynamics, or QP code.

The frozen 908-point query set (`5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2`) passed three exact static repeats on both external maps. SplaTAM: 5,464,102 Gaussians, finite h/gradient/Hessian, Hessian repeat exact, max relative symmetry error `1.39e-7`, and zero continuity outliers. Gaussian-SLAM: 3,045,467 Gaussians, the same finiteness/repeat results, max relative symmetry error `1.02e-7`, and zero continuity outliers. Both satisfy the internal G0 gate; this is not a public benchmark claim.

No controller, dynamics execution, QP, trajectory, navigation, SAFER rollout, G1, formal training, or V1R7 ran. The next task requires separate authorization for any G1 or downstream controller execution.
