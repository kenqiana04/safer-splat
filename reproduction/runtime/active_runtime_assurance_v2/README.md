# Active Runtime Assurance V2 implementation

This additive package implements the contracts frozen by PRs #107–#115 without changing production or reference source. It is an implementation-only, CPU-testable boundary and is **not authorized for rollout, benchmark, scientific outcome evaluation, real-time claims, or deployment claims**.

The 17 core modules use immutable typed runtime objects. `Supervisor.arbitrate` is the sole final action-selection authority, and `PlantCommitAdapter.commit` is the sole plant/dynamics authority. Candidate certification is ordered C0 → L2 → L3 after the once-per-cycle L1 result. The active geometry authority is controller radius 0.015 m, certification margin 0.010 m, effective radius 0.025 m, and `rho_seg=0`. Synthetic alternatives and goal-hold are disabled.

Validation is deterministic and CPU-only:

```text
python -B -m unittest discover -s reproduction/runtime/active_runtime_assurance_v2/tests -v
python -B reproduction/runtime/active_runtime_assurance_v2/model_check_active_runtime_implementation_v2.py
python -B reproduction/runtime/active_runtime_assurance_v2/validate_active_runtime_assurance_v2.py
```

The only authorized next task after this freeze is `VERIFY_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2`.
