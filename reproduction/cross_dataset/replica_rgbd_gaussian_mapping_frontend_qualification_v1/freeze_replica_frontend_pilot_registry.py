#!/usr/bin/env python3
"""Select the frozen 30-location train-only pilot without viewing RGB/depth."""
from __future__ import annotations

import hashlib
import json
import numpy as np

from _common import DATASET, ROOT, atomic_json, ensure_dirs, load_json, sha256_bytes, sha256_path

SEED = "REPLICA_MAPPING_FRONTEND_PILOT_V1"


def loc_hash(location_id: str) -> str:
    return hashlib.sha256(f"{SEED}:{location_id}".encode()).hexdigest()


def main() -> None:
    ensure_dirs(); frames = load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]
    by_location = {}
    for frame in frames:
        if frame["split"] == "train": by_location.setdefault(frame["location_id"], []).append(frame)
    if len(by_location) != 90: raise SystemExit("TRAIN_LOCATION_COUNT_MISMATCH")
    positions = {key: np.asarray(value[0]["camera_world_position"], dtype=np.float64) for key, value in by_location.items()}
    ordered = sorted(by_location, key=loc_hash); selected = [ordered[0]]
    while len(selected) < 30:
        remaining = [location for location in ordered if location not in selected]
        scores = {location: min(float(np.linalg.norm(positions[location] - positions[chosen])) for chosen in selected) for location in remaining}
        best = max(scores.values()); selected.append(min((location for location in remaining if scores[location] == best), key=loc_hash))
    mapping, holdout = [], []
    for location in selected:
        views = {int(row["yaw_offset_deg"]): row for row in by_location[location]}
        mapping += [views[0]["frame_id"], views[-60]["frame_id"]]; holdout.append(views[60]["frame_id"])
    core = {"seed": SEED, "selection_rule": "SHA-min initial location then float64 greedy farthest point with SHA tie-break", "source_manifest_sha256": sha256_path(DATASET / "formal_camera_manifest_v3.json"), "official_eval_usage_count": 0, "selected_location_ids": selected, "selected_location_positions_m": {key: positions[key].tolist() for key in selected}, "mapping_frame_ids": mapping, "holdout_frame_ids": holdout, "smoke_location_ids_unordered": None, "selection_script_sha256": sha256_path(__import__("pathlib").Path(__file__))}
    core["registry_sha256"] = sha256_bytes(json.dumps(core, sort_keys=True, separators=(",", ":")).encode())
    atomic_json(ROOT / "pilot_registry" / "replica_frontend_pilot_registry.json", core); print(core["registry_sha256"])


if __name__ == "__main__":
    main()
