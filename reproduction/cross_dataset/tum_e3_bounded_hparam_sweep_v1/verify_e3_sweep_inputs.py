"""Read-only identity gate for the frozen E3 sweep inputs and source snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


EXPECTED = {
    "v1r6_checkpoint": "4941bf1faba1aed31949ee4114898c0eec33ff1a46b7bcadad6d06f5f647ae6b",
    "v1r6_config": "c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe",
    "transforms": "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a",
    "metric_seed": "c5d69bbc965f16147842ad9813eca6d41d9556dd6af602e5b5049402a12e8b56",
    "e3_source": "96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947",
}
PATHS = {
    "v1r6_checkpoint": Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/nerfstudio_models/step-000029999.ckpt"),
    "v1r6_config": Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml"),
    "transforms": Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json"),
    "metric_seed": Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"path": str(path), "exists": path.is_file(), "size": path.stat().st_size if path.is_file() else None, "sha256": sha256(path) if path.is_file() else None}


def source_hash(root: Path) -> str:
    return hashlib.sha256(b"".join(path.read_bytes() for path in sorted(root.rglob("*.py")))).hexdigest()


def gpu_identity() -> dict[str, object]:
    command = ["nvidia-smi", "-i", "1", "--query-gpu=index,uuid,name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader"]
    try:
        value = subprocess.check_output(command, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        return {"available": False, "error": str(error)}
    return {"available": True, "query": value, "expected_uuid": "GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d", "uuid_match": "GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d" in value}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    files = {name: identity(path) for name, path in PATHS.items()}
    source = {"path": str(args.source_root), "exists": args.source_root.is_dir(), "sha256": source_hash(args.source_root) if args.source_root.is_dir() else None, "python_file_count": len(list(args.source_root.rglob("*.py"))) if args.source_root.is_dir() else 0}
    checks = {name: files[name]["sha256"] == expected for name, expected in EXPECTED.items() if name != "e3_source"}
    checks["e3_source"] = source["sha256"] == EXPECTED["e3_source"]
    result = {"expected": EXPECTED, "inputs": files, "source": source, "gpu": gpu_identity(), "checks": checks, "all_match": all(checks.values()), "status": "PASS" if all(checks.values()) else "BLOCKED_BY_E3_SWEEP_INPUT_IDENTITY_MISMATCH"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not result["all_match"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
