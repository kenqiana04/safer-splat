"""Server runtime test for train-only metadata injection is executed by the launcher."""
from __future__ import annotations

import numpy as np


def test_seed_npz_is_train_only_contract(seed_npz: str) -> None:
    seed = np.load(seed_npz)
    assert seed["xyz"].shape[0] > 0
    assert seed["xyz"].shape[0] == seed["rgb"].shape[0] == seed["train_frame_index"].shape[0]
    assert np.isfinite(seed["xyz"]).all()
    assert int(seed["train_frame_index"].max()) < 300
