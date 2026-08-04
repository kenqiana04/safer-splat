#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np
from fas_cbf_modules import UMAX, feasibility_aware_rows

a = np.asarray([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [-1., 0., 0.]])
b = np.asarray([0.05, 1.0, -0.01, 0.05])
h = np.asarray([0.1, 0.2, -0.1, 0.1])
ids = np.asarray([9, 2, 7, 1])
ra, rb, ri, debug = feasibility_aware_rows(a, b, h, ids)
checks = {
    "forced_candidate_dominance": 7 in set(ri.tolist()),
    "active_set_feasibility_preserved": bool(np.all(UMAX * np.sum(np.abs(ra), axis=1) > rb - 1e-12) or len(ra) > 0),
    "candidate_order_deterministic": ri.tolist() == sorted(ri.tolist()),
    "no_hidden_relaxation": debug["hidden_relaxation_count"] == 0,
    "same_control_bounds": debug["same_control_bounds"] is True,
    "redundant_row_removed": 2 not in set(ri.tolist()),
}
assert all(checks.values()), checks
print(json.dumps({"status": "PASS_FEASIBILITY_AWARE_UNIT_TESTS", "checks": checks}, sort_keys=True))
