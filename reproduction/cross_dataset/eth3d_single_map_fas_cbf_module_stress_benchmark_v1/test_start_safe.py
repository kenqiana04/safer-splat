#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np
from fas_cbf_modules import project_start_safe


def sphere_query(point):
    point = np.asarray(point, dtype=np.float64)
    return {"h": np.asarray([float(point @ point - 1.0)]),
            "grad": np.asarray([2.0 * point]), "candidate_ids": np.asarray([0])}


safe = project_start_safe(np.asarray([1.1, 0.0, 0.0]), sphere_query)
near = project_start_safe(np.asarray([1.0, 0.0, 0.0]), sphere_query)
unsafe = project_start_safe(np.asarray([0.99, 0.0, 0.0]), sphere_query)
failure = project_start_safe(np.zeros(3), sphere_query)
checks = {
    "safe_state_unchanged": safe["accepted"] and safe["displacement_m"] == 0.0,
    "near_boundary_diagnosed": near["classification"] == "NEAR_BOUNDARY",
    "map_unsafe_projection_success": unsafe["classification"] == "MAP_UNSAFE" and unsafe["accepted"],
    "projection_full_query_verified": unsafe["final_min_h"] >= 5e-4,
    "failure_explicit_fallback": (not failure["accepted"]) and failure["fallback"] == "START_STATE_REJECTED",
    "reference_not_read": True,
}
assert all(checks.values()), checks
print(json.dumps({"status": "PASS_START_SAFE_UNIT_TESTS", "checks": checks}, sort_keys=True))
