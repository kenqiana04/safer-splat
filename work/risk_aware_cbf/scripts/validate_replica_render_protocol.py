#!/usr/bin/env python3
"""Perform static checks before an external formal camera manifest is created."""
import argparse
import csv
import json
from pathlib import Path


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "passed", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    parser.add_argument("--pose-conversion", type=Path, required=True)
    parser.add_argument("--formal-output", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    protocol = args.protocol.read_text(encoding="utf-8") if args.protocol.is_file() else ""
    prereg = list(csv.DictReader(args.preregistration.open(encoding="utf-8"))) if args.preregistration.is_file() else []
    pose = json.loads(args.pose_conversion.read_text(encoding="utf-8")) if args.pose_conversion.is_file() else {}
    row = prereg[0] if prereg else {}
    checks = [
        ("protocol_file_exists", args.protocol.is_file(), str(args.protocol)),
        ("scene_fixed", row.get("scene") == "apartment_0", row.get("scene", "")),
        ("all_seeds_fixed", all(row.get(k) == "20260715" for k in ("random_seed", "numpy_seed", "python_random_seed", "habitat_pathfinder_seed")), "20260715"),
        ("spatial_locations_fixed", row.get("spatial_location_target") == "100", row.get("spatial_location_target", "")),
        ("yaw_order_fixed", row.get("yaw_offsets_deg") == "0;-60;60", row.get("yaw_offsets_deg", "")),
        ("sensor_complete", all(token in protocol for token in ("width `640`", "height `480`", "HFOV `90`", "near `0.05`", "far `20.0`")), "protocol literals"),
        ("height_fixed", row.get("camera_height") == "1.50", row.get("camera_height", "")),
        ("navmesh_fixed", row.get("navmesh") == "official_habitat_mesh_semantic.navmesh", row.get("navmesh", "")),
        ("pose_conversion_complete", bool(pose.get("T_nerfstudio_from_habitat_camera") and pose.get("T_habitat_from_nerfstudio_camera")), "matrix pair"),
        ("formal_output_empty", not args.formal_output.exists() or not any(args.formal_output.iterdir()), str(args.formal_output)),
        ("no_performance_parameters", "performance-driven" not in protocol.lower(), "protocol review"),
    ]
    rows = [{"check": name, "passed": passed, "detail": detail} for name, passed, detail in checks]
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "protocol_contract_checks.csv", rows)
    print("protocol_contract_passed=" + str(all(item[1] for item in checks)).lower())


if __name__ == "__main__":
    main()
