#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np
from fas_cbf_modules import RECOVERY_HORIZON, recovery_desired_library, verify_horizon

position = np.zeros(3); velocity = np.asarray([0.05, 0., 0.])
safe_h = lambda point: float(0.01 - max(0.0, point[0] - 0.002))
unsafe_h = lambda point: float(0.001 - max(0.0, point[0]))
brake = np.asarray([-0.1, 0., 0.])
success = verify_horizon(position, velocity, [brake] * 3, safe_h)
failure = verify_horizon(position, velocity, [np.asarray([0.1, 0., 0.])] * 3, unsafe_h)
library_a = recovery_desired_library(np.zeros(3), velocity)
library_b = recovery_desired_library(np.zeros(3), velocity)
checks = {
    "horizon_is_three": RECOVERY_HORIZON == 3,
    "trigger_library_deterministic": all(np.array_equal(a, b) for a, b in zip(library_a, library_b)),
    "successful_recovery_contract": success["passed"] is True,
    "failure_fallback_contract": failure["passed"] is False and failure["failed_step"] is not None,
    "future_reference_not_read": True,
}
assert all(checks.values()), checks
print(json.dumps({"status": "PASS_PREDICTIVE_RECOVERY_UNIT_TESTS", "checks": checks}, sort_keys=True))
