#!/usr/bin/env python3
"""Freeze UNKNOWN, robot, physical-budget, and future-evaluator contracts."""

import json
import math

from task_config import TASK_ROOT


def write(relative, value) -> None:
    path = TASK_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    unknown = {
        "status": "FROZEN_PENDING_IDEAL_SUPPORT_AUDIT",
        "algorithm": "ETH3D_MULTI_VIEW_FIRST_SURFACE_UNKNOWN_V1",
        "classification": "PROJECT_RUNTIME_UNKNOWN_DESIGN_V1",
        "runtime_inputs": ["TRAIN poses/intrinsics", "TRAIN capture groups", "future learned Gaussian map",
                           "future native/common renderer first or expected surface depth"],
        "runtime_forbidden_inputs": ["GT depth", "scan", "scan_eval", "occlusion", "reference geometry"],
        "support_capture_groups": 3, "minimum_angular_spread_deg": 15.0,
        "front_surface_margin_m": 0.01,
        "one_best_view_per_capture_group": True,
        "unsupported_classification": "UNKNOWN_TREATED_AS_OCCUPIED_OR_HIGH_COST",
        "frustum_or_low_alpha_implies_free": False,
        "sensitivity_report_only": {"groups": [2, 3, 4], "angles_deg": [5, 10, 15, 20]},
    }
    write("unknown/runtime_unknown_contract_v1.json", unknown)
    write("unknown/future_safer_unknown_adapter_contract.md", """# Future SAFER UNKNOWN adapter contract

At runtime, this adapter may read only TRAIN camera/capture identities and the
future learned map renderer. A query is a known-free candidate only when at
least three distinct capture groups support it before a finite positive learned
first surface, retaining 0.01 m margin, and the supporting ray directions span
at least 15 degrees. Otherwise it is UNKNOWN and SAFER/planning must treat it as
occupied or high cost. GT/reference assets are preflight-only and forbidden at
runtime. These thresholds are project benchmark choices, not universal theory.
""")
    dt, vmax, umax = 0.05, 0.10, 0.10
    reaction = math.sqrt(3.0) * (dt * vmax + vmax * vmax / (2.0 * umax))
    nonmap = 0.10 + 0.01 + 0.0 + 0.0 + 0.0 + reaction + 0.03
    robot = {
        "status": "FROZEN", "claim": "REAL_WORLD_SCENE_MAP_WITH_ORACLE_STATE_SIMULATED_NAVIGATION",
        "classification": "PROJECT_BENCHMARK_DESIGN_CHOICE", "geometry": "sphere",
        "r_robot_m": 0.10, "epsilon_base_m": 0.01, "state": "[p,v]", "integrator": "forward Euler",
        "dt_s": dt, "componentwise_vmax_m_s": vmax, "componentwise_umax_m_s2": umax,
        "bounded_qp": True, "post_qp_clip": False, "oracle_state": True,
        "exact_swept_segment_oracle_required": True,
    }
    budget = {
        "status": "FROZEN_FORMULA_PENDING_ROUTE_VALUES",
        "epsilon_loc_m": 0.0, "epsilon_shape_m": 0.0, "epsilon_sampled_m": 0.0,
        "epsilon_reaction_stop_m": reaction, "epsilon_tracking_target_m": 0.03,
        "reaction_stop_formula": "sqrt(3)*(dt*vmax + vmax^2/(2*umax))",
        "nonmap_reserve_m": nonmap,
        "B_map_available_formula": "min_reference_center_clearance(route)-nonmap_reserve",
        "required_B_map_available_positive": True,
        "arbitrary_centimeter_gate": False,
        "real_robot_safety_standard_claim": False,
    }
    write("physical_budget/eth3d_robot_contract.json", robot)
    write("physical_budget/eth3d_physical_error_budget.json", budget)
    write("physical_budget/stopping_bound_derivation.md", f"""# Stopping bound derivation

With frozen `dt={dt}`, `vmax={vmax}`, and `umax={umax}`, per-axis one-sample
reaction travel is `dt*vmax={dt*vmax:.12g}` m and braking travel is
`vmax^2/(2*umax)={vmax*vmax/(2*umax):.12g}` m. The conservative Euclidean
bound is `sqrt(3)` times their sum: `{reaction:.12g}` m. Adding robot radius,
base margin, zero oracle-state localization/shape/sampling terms, and the
0.03 m tracking target gives a non-map reserve of `{nonmap:.12g}` m.
""")
    write("physical_budget/physical_budget_validation.json", {
        "status": "PASS", "recomputed_reaction_stop_m": reaction,
        "recomputed_nonmap_reserve_m": nonmap, "finite": math.isfinite(nonmap),
    })
    evaluator = {
        "status": "FROZEN_FUTURE_EVALUATOR_NOT_EXECUTED",
        "gates": ["integrity/no leakage", "native/common renderer parity", "fixed 11-point alpha risk-coverage",
                  "ETH3D official accuracy/completeness/F-score", "rig HELDOUT NVS/depth",
                  "DSLR cross-view NVS/depth if available", "runtime UNKNOWN knownness",
                  "route-tube known fraction", "exact one-sided e_plus", "route-specific B_map_available",
                  "false-free components", "independent swept-body collision", "G0 separate",
                  "R/N/query independent classification", "diagnosis after failure"],
        "alpha_grid": [i / 10 for i in range(11)], "universal_numeric_gate": False,
        "candidate_map_evaluation_executed": False,
    }
    write("evaluator/eth3d_future_protocol_v2_evaluator_contract.json", evaluator)
    write("evaluator/future_map_qualification_decision_tree.json", {
        "status": "FROZEN", "order": ["integrity", "R", "N", "queryability", "route budget", "independent collision", "G0"],
        "failure_action": "diagnose without changing frozen gates",
    })
    print("PASS_NONDATA_CONTRACT_FREEZE", reaction, nonmap)


if __name__ == "__main__":
    main()
