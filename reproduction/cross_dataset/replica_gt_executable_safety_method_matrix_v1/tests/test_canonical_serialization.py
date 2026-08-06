import numpy as np
from alternative_library.canonical_serialization import canonical_float, canonical_sha256
from task_config import PROPERTY_SEED, SERIALIZATION_CASES


def test_signed_zero_and_random_float64_serialization_are_stable():
    assert canonical_float(-0.0) == canonical_float(0.0) == "0x0.0p+0"
    rng = np.random.default_rng(PROPERTY_SEED)
    values = rng.normal(size=SERIALIZATION_CASES)
    for value in values:
        assert canonical_float(float(value)) == canonical_float(float(value))
    payload = {"values": tuple(float(value) for value in values[:64]), "zero": -0.0}
    assert canonical_sha256(payload) == canonical_sha256(payload)
