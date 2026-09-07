import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, SupervisorDecision, make_action
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i+3] if i < 3 else control[i-3]) for i in range(6))


class PlantCommitTests(unittest.TestCase):
    def setUp(self):
        self.state=snapshot(); self.registry=AuthorityRegistry.frozen(self.state.map_identity,"dt:0.05")
        self.plant=PlantCommitAdapter(self.registry,transition)

    def test_selected_equals_executed(self):
        action=make_action((0.01,0,0),ActionRole.PRIMARY_NAVIGATION,"candidate:1")
        decision=SupervisorDecision(0,self.state.identity,action,True,"NAV","ARB_NAV")
        receipt=self.plant.commit(decision,self.state,action)
        self.assertTrue(receipt.committed)
        self.assertEqual(receipt.selected_action_identity,receipt.executed_action_identity)
        self.assertEqual(receipt.exact_vector,action.vector)

    def test_boundary_never_steps_plant(self):
        action=make_action((0,0,0),ActionRole.ASSURANCE_BOUNDARY_NO_ACTION,"boundary")
        decision=SupervisorDecision(0,self.state.identity,None,False,"BOUNDARY","ARB_BOUNDARY")
        with self.assertRaises(CommitAuthorityViolation): self.plant.commit(decision,self.state,action)

    def test_identity_mismatch_rejected(self):
        selected=make_action((0.01,0,0),ActionRole.PRIMARY_NAVIGATION,"a")
        other=make_action((0.02,0,0),ActionRole.PRIMARY_NAVIGATION,"b")
        decision=SupervisorDecision(0,self.state.identity,selected,True,"NAV","ARB_NAV")
        with self.assertRaises(CommitAuthorityViolation): self.plant.commit(decision,self.state,other)

    def test_bypass_delegates_exact_reference_action_without_active_admission(self):
        reference=make_action((0.09999999403953552,0.10000000149011612,-0.031203344464302063),ActionRole.PRIMARY_NAVIGATION,"reference")
        decision=SupervisorDecision(0,self.state.identity,reference,True,"BYPASS_REFERENCE_ACTION_UNCHANGED","BYPASS")
        receipt=self.plant.commit(decision,self.state,reference)
        self.assertTrue(receipt.committed)
        self.assertEqual(receipt.exact_vector,reference.vector)

    def test_active_rule_still_rejects_same_out_of_box_action(self):
        candidate=make_action((0.09999999403953552,0.10000000149011612,-0.031203344464302063),ActionRole.PRIMARY_NAVIGATION,"candidate")
        decision=SupervisorDecision(0,self.state.identity,candidate,True,"NAV","ARB_NAV")
        with self.assertRaisesRegex(CommitAuthorityViolation,"ACTUATOR_ADMISSION_REQUIRED"):
            self.plant.commit(decision,self.state,candidate)


if __name__ == "__main__": unittest.main()
