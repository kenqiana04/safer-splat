import tempfile
import unittest

from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import DeadlineProfileRequired
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, RuntimeMode, make_action
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i+3] if i < 3 else control[i-3]) for i in range(6))


class ActiveRunnerTests(unittest.TestCase):
    def build(self,mode,profile=None):
        state=snapshot(); registry=AuthorityRegistry.frozen(state.map_identity,"dt:0.05",None if profile is None else profile.identity)
        return ActiveRunner(mode,registry,Supervisor(registry),PlantCommitAdapter(registry,transition),BackupTokenStore(),TraceWriter("trial-1"),profile)

    def test_active_missing_profile_rejected_before_trial(self):
        with self.assertRaises(DeadlineProfileRequired): self.build(RuntimeMode.ACTIVE_RUNTIME_ON).startup()

    def test_bypass_preserves_reference_action(self):
        runner=self.build(RuntimeMode.ACTIVE_HARNESS_BYPASS); runner.startup()
        state=snapshot(); action=make_action((0.01,0,0),ActionRole.PRIMARY_NAVIGATION,"reference")
        receipt=runner.commit_bypass(state,action)
        self.assertEqual(receipt.exact_vector,action.vector)

    def test_active_profile_allows_startup_not_rollout(self):
        profile=RuntimeDeadlineProfile.create(1.0,(),0.1,0.9,"fake")
        runner=self.build(RuntimeMode.ACTIVE_RUNTIME_ON,profile)
        runner.startup()
        self.assertTrue(runner.started)


if __name__ == "__main__": unittest.main()
