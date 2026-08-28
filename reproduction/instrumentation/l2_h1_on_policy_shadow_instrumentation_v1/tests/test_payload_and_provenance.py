from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from candidate_provenance import (  # noqa: E402
    NATIVE_SIBLING_CONTROL,
    NOMINAL_REFERENCE,
    SELECTED_EXECUTED_CONTROL,
    make_native_sibling,
    make_nominal_reference,
)
from immutable_payload import build_immutable_payload  # noqa: E402
from reachability_capture import baseline_commit_facts  # noqa: E402


class FakeTensor:
    def __init__(self, values, device="cuda:0", dtype="float32"):
        self.values = list(values)
        self.device = device
        self.dtype = dtype

    def detach(self):
        return self

    def to(self, device):
        return FakeTensor(self.values, device=device, dtype=self.dtype)

    def contiguous(self):
        return self

    def numpy(self):
        return list(self.values)


def payload(*, x=None, u=None, u_des=None, siblings=()):
    return build_immutable_payload(
        run_id="unit-run",
        trial_id="unit-trial",
        step_id=4,
        payload_sequence_id=7,
        x_k=[1, 2, 3, 0.1, 0.2, 0.3] if x is None else x,
        dt=0.05,
        selected_u=[0.2, -0.1, 0.0] if u is None else u,
        u_des=[0.3, -0.2, 0.1] if u_des is None else u_des,
        selected_candidate_id="selected-4",
        selected_candidate_source="FROZEN_CBF_SOLVE_QP_SUCCESS_OUTPUT",
        map_authority_id="map-id",
        reachability=baseline_commit_facts(True),
        native_siblings=siblings,
    )


class PayloadAndProvenanceTests(unittest.TestCase):
    def test_snapshots_are_immutable_and_do_not_alias_sources(self):
        x = [1, 2, 3, 0.1, 0.2, 0.3]
        u = [0.2, -0.1, 0.0]
        u_des = [0.3, -0.2, 0.1]
        value = payload(x=x, u=u, u_des=u_des)
        original_hash = value.semantic_hash
        x[:] = [99] * 6
        u[:] = [99] * 3
        u_des[:] = [99] * 3
        self.assertEqual(value.x_k[0], 1.0)
        self.assertEqual(value.selected_candidate.u, (0.2, -0.1, 0.0))
        self.assertEqual(value.nominal_reference.u, (0.3, -0.2, 0.1))
        self.assertEqual(value.semantic_hash, original_hash)
        with self.assertRaises(FrozenInstanceError):
            value.dt = 0.1  # type: ignore[misc]

    def test_cuda_capture_is_an_explicit_cpu_copy(self):
        value = payload(
            x=FakeTensor([1, 2, 3, 0.1, 0.2, 0.3]),
            u=FakeTensor([0.2, -0.1, 0.0]),
            u_des=FakeTensor([0.3, -0.2, 0.1]),
        )
        self.assertEqual(value.capture_device, "cuda:0")
        self.assertEqual(value.capture_copy_mode, "DETACH_DEVICE_TO_CPU_CONTIGUOUS_COPY")
        self.assertTrue(value.synchronization_required)
        self.assertIsInstance(value.x_k, tuple)

    def test_u_des_is_reference_not_native_alternative(self):
        value = payload()
        self.assertEqual(value.selected_candidate.candidate_role, SELECTED_EXECUTED_CONTROL)
        self.assertEqual(value.nominal_reference.candidate_role, NOMINAL_REFERENCE)
        self.assertEqual(value.native_candidate_group_size, 1)
        self.assertEqual(value.native_sibling_candidates, ())
        invalid = make_nominal_reference("bad", "unit", [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "native sibling"):
            payload(siblings=(invalid,))

    def test_preexisting_native_sibling_is_secondary_only(self):
        sibling = make_native_sibling("sibling", "FROZEN_RUNTIME_CANDIDATE", [0.0, 0.1, 0.2])
        value = payload(siblings=(sibling,))
        self.assertEqual(value.native_candidate_group_size, 2)
        self.assertEqual(value.native_sibling_candidates[0].candidate_role, NATIVE_SIBLING_CONTROL)
        self.assertFalse(value.native_sibling_candidates[0].selected_for_execution)


if __name__ == "__main__":
    unittest.main()
