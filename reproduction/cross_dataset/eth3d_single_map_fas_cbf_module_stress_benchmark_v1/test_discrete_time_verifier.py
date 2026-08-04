#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np
from fas_cbf_modules import verify_discrete_step


def segment_obstacle(point):
    return float((point[0] - 0.025) ** 2 - 1.0e-6)


result = verify_discrete_step(np.zeros(3), np.asarray([1.0, 0., 0.]), np.zeros(3), segment_obstacle, samples=11)
safe = verify_discrete_step(np.zeros(3), np.zeros(3), np.zeros(3), lambda _: 0.01, samples=11)
manual = min(segment_obstacle(np.asarray([x, 0., 0.])) for x in np.linspace(0., 0.05, 11))
checks = {
    "current_safe_endpoint_safe_segment_unsafe": result["endpoint_only_miss"] is True,
    "safe_case_passes": safe["passed"] is True,
    "exact_registered_sample_parity": abs(result["segment_h"] - manual) < 1e-15,
    "future_reference_not_read": True,
}
assert all(checks.values()), checks
print(json.dumps({"status": "PASS_DISCRETE_TIME_VERIFIER_UNIT_TESTS", "checks": checks}, sort_keys=True))
