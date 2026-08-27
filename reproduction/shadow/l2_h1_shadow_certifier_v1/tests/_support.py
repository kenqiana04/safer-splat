from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))


def assert_tuple_allclose(testcase, actual, expected, atol=1e-12):
    np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), rtol=0.0, atol=atol)
