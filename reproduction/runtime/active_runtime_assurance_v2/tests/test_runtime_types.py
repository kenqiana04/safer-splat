import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    RuntimeStateSnapshot,
    canonical_sha256,
    make_action,
)


class RuntimeTypesTests(unittest.TestCase):
    def test_canonical_identity_stable_and_sensitive(self):
        payload = {"vector": (0.0, -0.0, 0.1), "role": "PRIMARY_NAVIGATION"}
        self.assertEqual(canonical_sha256(payload), canonical_sha256(payload))
        self.assertNotEqual(canonical_sha256(payload), canonical_sha256({**payload, "role": "CERTIFIED_TERMINAL"}))

    def test_role_changes_action_identity_even_for_zero(self):
        primary = make_action((0.0, 0.0, 0.0), ActionRole.PRIMARY_NAVIGATION, "candidate:1")
        terminal = make_action((0.0, 0.0, 0.0), ActionRole.CERTIFIED_TERMINAL, "terminal:1")
        self.assertNotEqual(primary.identity, terminal.identity)

    def test_state_change_changes_identity(self):
        a = RuntimeStateSnapshot.create("t", 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map", 0.05)
        b = RuntimeStateSnapshot.create("t", 0, (0, 0, 0, 0, 0, 1e-300), (1, 0, 0, 0, 0, 0), "map", 0.05)
        self.assertNotEqual(a.identity, b.identity)


if __name__ == "__main__": unittest.main()
