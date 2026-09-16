from __future__ import annotations

import unittest

from reproduction.runtime.active_runtime_assurance_v2.plant_commit import _reference_transition
from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import (
    CanonicalExecutionTransition,
    NEUTRAL_ACTION,
    binary32_hex,
)


class CanonicalTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transition = CanonicalExecutionTransition("cpu", backend_label="TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY")
        self.states = (
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            (0.1, -0.2, 0.3, 0.01, -0.02, 0.03),
            (-0.1437879502773285, 0.1240079328417778, 0.04031834751367569, 8.934789264003484e-08, -1.3920173103088018e-07, 2.0614740137148146e-08),
            (1.17549435e-38, -1.17549435e-38, 0.015, 0.1, -0.1, 1.1920929e-07),
            (0.4999999701976776, -0.4999999701976776, 0.0, -0.09999999403953552, 0.09999999403953552, 0.0),
        )
        self.actions = (
            NEUTRAL_ACTION,
            (-0.1, -0.1, -0.1),
            (0.1, 0.1, 0.1),
            (0.1, -0.1, 0.03125),
        )

    def test_matches_frozen_plant_reference_bitwise(self) -> None:
        for state in self.states:
            for action in self.actions:
                expected = _reference_transition(state, action, 0.05)
                actual = self.transition.transition(state, action, 0.05)
                self.assertEqual(binary32_hex(actual), binary32_hex(expected))

    def test_l1_position_is_action_independent(self) -> None:
        for state in self.states:
            endpoints = {binary32_hex(self.transition.transition(state, action, 0.05)[:3]) for action in self.actions}
            self.assertEqual(len(endpoints), 1)
            self.assertEqual(next(iter(endpoints)), binary32_hex(self.transition.immediate_position(state, 0.05)))

    def test_l2_causal_horizon_and_second_action_irrelevance(self) -> None:
        state = self.states[1]
        first_zero, second_zero = self.transition.two_step(state, NEUTRAL_ACTION, 0.05)
        first_control, second_control = self.transition.two_step(state, (0.1, -0.1, 0.05), 0.05)
        self.assertEqual(binary32_hex(first_zero.post_state[:3]), binary32_hex(first_control.post_state[:3]))
        self.assertNotEqual(binary32_hex(second_zero.post_state[:3]), binary32_hex(second_control.post_state[:3]))
        endpoints = {
            binary32_hex(self.transition.two_step(state, (0.1, -0.1, 0.05), 0.05, second_action)[1].post_state[:3])
            for second_action in self.actions
        }
        self.assertEqual(len(endpoints), 1)


if __name__ == "__main__":
    unittest.main()
