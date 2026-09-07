import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, RuntimeStateSnapshot, SupervisorDecision, make_action
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import make_canonical_trial_identity


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i + 3] if i < 3 else control[i - 3]) for i in range(6))


class BypassPlantCommitRegressionTests(unittest.TestCase):
    def setUp(self):
        trial_id = make_canonical_trial_identity(50).canonical_trial_id
        self.snapshot = RuntimeStateSnapshot.create(trial_id, 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map:fixture", 0.05)
        self.registry = AuthorityRegistry.frozen(self.snapshot.map_identity, "RUN_PY_DT_0P05")
        self.action = make_action((0.09999999403953552, 0.10000000149011612, -0.031203344464302063), ActionRole.PRIMARY_NAVIGATION, "reference")

    def test_bypass_delegates_exact_reference_bits(self):
        plant = PlantCommitAdapter(self.registry, transition)
        decision = Supervisor(self.registry).bypass_decision(self.snapshot, self.action)
        receipt = plant.commit(decision, self.snapshot, self.action)
        self.assertEqual(receipt.exact_vector, self.action.vector)
        self.assertEqual(receipt.selected_action_identity, receipt.executed_action_identity)

    def test_non_bypass_guard_remains_strict(self):
        plant = PlantCommitAdapter(self.registry, transition)
        decision = SupervisorDecision(0, self.snapshot.identity, self.action, True, "NAV", "ARB_NAV")
        with self.assertRaisesRegex(CommitAuthorityViolation, "ACTUATOR_ADMISSION_REQUIRED"):
            plant.commit(decision, self.snapshot, self.action)


if __name__ == "__main__":
    unittest.main()
