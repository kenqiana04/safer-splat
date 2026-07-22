# TUM SplaTAM Original SAFER G1 Smoke V1

## Result

`BLOCKED_BY_TUM_SPLATAM_G1_INPUT_IDENTITY_MISMATCH`

PR #44 is Open Draft at `f63b4c496861c4f8881348d74244c1ff9a528d51`. Its required frozen runtime blobs are `d7f17b67df40e36e458c7a5ed77c4a04659c6f35` for `splat/distances.py`, `782c38eca50e78c605085b481155ed61e4607336` for `splat/gsplat_utils.py`, and Numerical Contract V2 blob `7a0d85b0b334c2e94ccc23b033d8453322d72fe1`.

The authoritative 4090 checkout `/disk1/zlab/projects/safer-splat` instead reports head `57c55485e357343c3d166a9123ab9a9275c12067`, old pre-correction blobs `81940ca59297a2ee3b4214901b038725c2748318` and `4e704349ddb5b5d6737e38d63965699ecfe81030`, and does not contain the expected V2 contract path. `cbf/cbf_utils.py` matches the required blob, and the TUM transforms SHA-256 matches, but all required identities must match.

No map load, query, filter, dynamics, CBF-QP, one-step QP, rollout, or diagnostic trial was started. No Start-Safe, Risk-Aware, Discrete-Time Verification, Predictive Recovery, 20/100-trial benchmark, formal training, or V1R7 was started.

The required next action is a separate server-checkout synchronization and identity-verification task that brings `/disk1/zlab/projects/safer-splat` exactly to PR #44 head without overwriting unrelated work. Only after a new explicit preflight confirms all frozen blobs may this G1 smoke protocol be reauthorized.
