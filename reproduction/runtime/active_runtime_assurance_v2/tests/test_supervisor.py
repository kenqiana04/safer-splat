import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, CandidateRole, CertificateStatus, DeadlineObservation, DeadlineStatus,
    L3Result, PreparedBackupBundle, TerminalResult, make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


def deadline(status=DeadlineStatus.OPEN):
    return DeadlineObservation(status,"ARBITRATION",0.0,1.0,"deadline:test")


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.state=snapshot(); self.registry=AuthorityRegistry.frozen(self.state.map_identity,"dt:0.05")
        self.supervisor=Supervisor(self.registry)
        self.candidate=make_candidate((0.0,0.0,0.0),CandidateRole.PRIMARY,"PRIMARY_NATIVE_CBF_QP","cbf",self.state)
        self.bundle=PreparedBackupBundle.create(self.candidate,self.state,(((0,0,0),"backup:0"),),self.registry.geometry.identity.value,self.registry.actuator.identity.value,self.registry.dynamics.identity.value,"terminal:ref")
        self.l3=L3Result(CertificateStatus.PASS,"WITNESS",self.candidate.identity,self.bundle,"l3:e")

    def test_navigation_priority_and_zero_role(self):
        terminal=TerminalResult(CertificateStatus.PASS,"OK",True,None,"term:e")
        decision=self.supervisor.arbitrate(self.state,self.candidate,self.l3,None,False,terminal,deadline())
        self.assertEqual(decision.selected_action.role,ActionRole.PRIMARY_NAVIGATION)
        self.assertIs(decision.prepared_bundle,self.bundle)

    def test_valid_backup_outranks_terminal(self):
        # A minimal active-token fixture is provided by the store test; here use the direct action seam.
        backup=self.supervisor.make_retained_backup_action((0,0,0),"backup:0")
        terminal=TerminalResult(CertificateStatus.PASS,"OK",True,None,"term:e")
        decision=self.supervisor.arbitrate(self.state,None,None,backup,True,terminal,deadline())
        self.assertEqual(decision.selected_action.role,ActionRole.RETAINED_BACKUP)

    def test_expired_still_allows_valid_backup_but_no_navigation(self):
        backup=self.supervisor.make_retained_backup_action((0,0,0),"backup:0")
        decision=self.supervisor.arbitrate(self.state,self.candidate,self.l3,backup,True,None,deadline(DeadlineStatus.EXPIRED))
        self.assertEqual(decision.selected_action.role,ActionRole.RETAINED_BACKUP)

    def test_terminal_role_assigned_only_here(self):
        terminal=TerminalResult(CertificateStatus.PASS,"OK",True,None,"term:e")
        decision=self.supervisor.arbitrate(self.state,None,None,None,False,terminal,deadline())
        self.assertEqual(decision.selected_action.role,ActionRole.CERTIFIED_TERMINAL)

    def test_boundary_has_no_executable_action(self):
        decision=self.supervisor.arbitrate(self.state,None,None,None,False,None,deadline())
        self.assertFalse(decision.allows_commit)
        self.assertIsNone(decision.selected_action)


if __name__ == "__main__": unittest.main()
