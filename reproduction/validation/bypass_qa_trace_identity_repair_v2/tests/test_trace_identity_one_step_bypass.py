import tempfile
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import TraceFinalizedError
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, RuntimeMode, RuntimeStateSnapshot, make_action
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import make_canonical_trial_identity


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i + 3] if i < 3 else control[i - 3]) for i in range(6))


class TraceIdentityOneStepBypassTests(unittest.TestCase):
    def test_real_bypass_commit_appends_and_finalizes_one_record(self):
        identity = make_canonical_trial_identity(50)
        snapshot = RuntimeStateSnapshot.create(identity.canonical_trial_id, 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map:fixture", 0.05)
        registry = AuthorityRegistry.frozen(snapshot.map_identity, "RUN_PY_DT_0P05")
        action = make_action((0.01, 0.0, 0.0), ActionRole.PRIMARY_NAVIGATION, "reference:fixture")
        with tempfile.TemporaryDirectory() as tmp:
            writer = TraceWriter(identity.canonical_trial_id, Path(tmp))
            plant = PlantCommitAdapter(registry, transition)
            runner = ActiveRunner(RuntimeMode.ACTIVE_HARNESS_BYPASS, registry, Supervisor(registry), plant, BackupTokenStore(), writer)
            runner.startup()
            receipt = runner.commit_bypass(snapshot, action)
            lock = runner.finalize_trace()
            self.assertEqual(plant.commit_count, 1)
            self.assertEqual(len(writer.records), 1)
            self.assertEqual(snapshot.trial_id, writer.trial_id)
            self.assertEqual(writer.records[0].trial_id, identity.canonical_trial_id)
            self.assertEqual(lock.trial_id, identity.canonical_trial_id)
            self.assertEqual(lock.record_count, 1)
            self.assertEqual(receipt.selected_action_identity, receipt.executed_action_identity)
            with self.assertRaisesRegex(TraceFinalizedError, "TRACE_ALREADY_FINALIZED"):
                writer.append(writer.records[0])


if __name__ == "__main__":
    unittest.main()
