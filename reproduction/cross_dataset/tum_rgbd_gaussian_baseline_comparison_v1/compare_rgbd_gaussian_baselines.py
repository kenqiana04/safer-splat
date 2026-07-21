"""Apply the preregistered comparison rule without changing the 0.75 gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


INTERNAL = [
    {"method": "INTERNAL_TUNED_C_L050_K2000_B020", "AbsRel": .188127, "RMSE": .477082, "delta1": .685632, "ratio": .992987, "static_audit": "PASS", "G0": "FAIL_delta1_lt_0.75"},
    {"method": "INTERNAL_S2_POINT_TO_PLANE", "AbsRel": .197457, "RMSE": .499080, "delta1": .671166, "ratio": .996289, "static_audit": "PASS", "G0": "FAIL_delta1_lt_0.75"},
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_native_metrics(result: dict) -> dict:
    """Preserve source result fields while giving the table stable names."""
    aliases = {"AbsRel": "absrel", "SqRel": "sqrel", "RMSE": "rmse", "RMSE_log": "rmselog"}
    normalized = dict(result)
    for canonical, native in aliases.items():
        if canonical not in normalized and native in normalized:
            normalized[canonical] = normalized[native]
    return normalized


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--splatam", type=Path, required=True); p.add_argument("--gaussian-slam", type=Path, required=True); p.add_argument("--comparability", type=Path, required=True); p.add_argument("--primary", type=Path, required=True); p.add_argument("--system", type=Path, required=True); p.add_argument("--gate", type=Path, required=True); p.add_argument("--handoff", type=Path, required=True); a = p.parse_args()
    comp, splat, gslam = load(a.comparability), normalize_native_metrics(load(a.splatam)), normalize_native_metrics(load(a.gaussian_slam))
    primary = list(INTERNAL); system = []
    for label, result in (("SPLATAM_GTPOSE_MAP_ONLY", splat), ("GAUSSIAN_SLAM_GTPOSE_MAP_ONLY", gslam)):
        classification = comp[label]["classification"]
        if classification == "MAP_ONLY_COMPARABLE" and result.get("status") == "PASS":
            primary.append({"method": label, **result})
        else:
            system.append({"method": label, "classification": classification, **result})
    external = [x for x in primary if x["method"].startswith(("SPLATAM", "GAUSSIAN"))]
    if not external:
        status, next_task = "TUM_RGBD_BASELINE_COMPARISON_NO_MAP_ONLY_BASELINE_COMPLETED", "diagnose source/environment/protocol blocker"
    else:
        best = min(external, key=lambda x: x["AbsRel"])
        g0 = [x for x in external if x["delta1"] >= .75 and x["AbsRel"] <= .25 and x.get("static_audit") == "PASS"]
        superior = [x for x in external if x["delta1"] >= .725632 and x["AbsRel"] <= .198127]
        competitive = [x for x in external if abs(x["delta1"]-.685632)<.04 and abs(x["AbsRel"]-.188127)<.03]
        if g0: status, next_task = "PASS_TUM_DEDICATED_RGBD_BASELINE_G0_ACCEPTABLE", "TUM Dedicated RGB-D Gaussian Map Adapter Integration V1"
        elif superior: status, next_task = "PASS_TUM_DEDICATED_RGBD_BASELINE_DEGRADED_SUPERIOR", "TUM Dedicated RGB-D Mapper Adaptation and Metric-Gate Calibration V1"
        elif competitive: status, next_task = "PASS_TUM_INTERNAL_PIPELINE_COMPETITIVE_WITH_RGBD_BASELINES", "TUM Multi-Sequence Geometry-Gate Calibration V1"
        else: status, next_task = "TUM_RGBD_BASELINE_COMPARISON_NO_MAP_ONLY_BASELINE_COMPLETED", "diagnose source/environment/protocol blocker"
    a.primary.write_text(json.dumps({"rows": primary, "primary_table_excludes_system_level": True}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    a.system.write_text(json.dumps({"rows": system, "not_used_for_G0_ranking": True}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    gate = {"status": status, "threshold_delta1": .75, "threshold_changed": False, "formal_training": False, "navigation": False, "SAFER_rollout": False, "G1": False}
    a.gate.write_text(json.dumps(gate, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    a.handoff.write_text(json.dumps({"status": status, "recommended_next_task": next_task, "automatic_follow_on_started": False}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(gate, sort_keys=True))


if __name__ == "__main__": main()
