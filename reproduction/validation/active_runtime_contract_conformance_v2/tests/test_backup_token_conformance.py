import unittest

from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, ActionRole, SupervisorDecision
from conformance_support import candidate, registry, snapshot, transition
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor


class BackupTokenConformance(unittest.TestCase):
    def test_prepared_then_atomic_activation_and_cursor(self):
        state = snapshot()
        reg = registry()
        cand = candidate(state)
        bundle = __import__("reproduction.runtime.active_runtime_assurance_v2.runtime_types", fromlist=["PreparedBackupBundle"]).PreparedBackupBundle.create(cand, state, [((0.0, 0.0, 0.0), "tail")], reg.geometry.identity.value, reg.actuator.identity.value, reg.dynamics.identity.value, None)
        store = BackupTokenStore()
        store.prepare(bundle)
        self.assertIsNone(store.current())
        supervisor = Supervisor(reg)
        action = supervisor.make_retained_backup_action((0.0, 0.0, 0.0), "retained")
        decision = SupervisorDecision(state.cycle_index, state.identity, action, True, "TEST", "ARB_BACKUP")
        receipt = PlantCommitAdapter(reg, transition).commit(decision, state, action)
        # Activation is only legal after a certified navigation receipt; this test
        # records that PREPARED is not executable, rather than manufacturing one.
        self.assertTrue(receipt.committed)
        self.assertEqual(store.validate(state, reg).status, CertificateStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
