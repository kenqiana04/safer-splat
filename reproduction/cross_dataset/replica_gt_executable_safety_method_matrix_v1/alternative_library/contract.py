"""Static, versioned directional-library contract without outcome semantics."""
from __future__ import annotations

from task_config import DEDUP_ABS_TOL, DT, LIBRARY_ID, LIBRARY_SOURCE, LIBRARY_VERSION, NORMAL_EPSILON, SLOT_IDS, U_BOUND


def contract_payload() -> dict[str, object]:
    return {
        "library_id": LIBRARY_ID, "library_version": LIBRARY_VERSION, "source": LIBRARY_SOURCE,
        "template_slot_count": 6, "max_available_control_count": 6, "slot_ids": list(SLOT_IDS),
        "normal": "n=(p-c_j)/||p-c_j||_2; c_j comes from active_gaussian_ids[0] of the current represented-map FULL query",
        "normal_epsilon": NORMAL_EPSILON, "goal_tangent_fallback": "argmin(|axis^T n|) over e_x,e_y,e_z with x,y,z tie order",
        "box_scaling": "u_box(d)=0.1*d/||d||_infinity", "deceleration_projection": "project d_raw into {d | v^T d <= 0}",
        "dedup_rule": {"order": list(SLOT_IDS), "abs_component_tolerance": DEDUP_ABS_TOL, "earlier_slot_wins": True},
        "canonical_float": "float64.hex; signed zero normalized to 0x0.0p+0", "dt": DT, "u_bound": U_BOUND,
        "forbidden_inputs": ["official_mesh", "reference_collision", "future_outcome", "G0_G5", "method_success", "progress", "runtime", "benchmark_registry", "oracle"],
    }
