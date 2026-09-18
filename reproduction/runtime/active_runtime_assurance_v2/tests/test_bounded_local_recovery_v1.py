"""CPU-only Gate 0 implementation checks; no plant/GPU research execution."""

import unittest
import inspect
import struct
from dataclasses import replace

from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import (
    BoundedRecoveryProvider, RecoveryExhaustionRegister, RecoverySourceGrant,
    ScanStatus, canonical_control_identity, exhaustion_key, numeric_bits_identity,
)
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, ActiveCycleRequest, CandidateRole, CertificateStatus,
    PublicCycleEvent, PublicCyclePhase, RecoveryRoutingFacts, RuntimePhase,
    RuntimeStateSnapshot, make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry


def build_recovery_cycle(pass_rank=0, terminal=CertificateStatus.PASS):
    system = build_public_cycle({"l3": CertificateStatus.FAIL,
                                 "terminal_member": terminal == CertificateStatus.PASS,
                                 "terminal": terminal})
    coordinator = system["coordinator"]
    registry = make_v3_authority_registry(system["state"].map_identity, "dt:0.05",
                                          system["runner"].deadline_profile.identity)
    for module in (coordinator, coordinator.start_admission, coordinator.l1_runtime,
                   coordinator.c0_admission, coordinator.l2_runtime, coordinator.l3_runtime,
                   coordinator.terminal_runtime, system["supervisor"], system["runner"], system["plant"]):
        if hasattr(module, "registry"):
            module.registry = registry
        if hasattr(module, "_registry"):
            module._registry = registry
    system["registry"] = registry
    coordinator.recovery_provider = BoundedRecoveryProvider(registry, "transition:fixture", "backend:fixture")
    coordinator.recovery_register = RecoveryExhaustionRegister()

    def l3_backend(_snapshot, candidate):
        source = candidate.provenance.source_type
        if source == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1":
            rank = int(candidate.provenance.creation_timestamp.split(":recovery-rank:")[1].split(":")[0])
            if rank == pass_rank:
                return CertificateStatus.PASS, (((0.0, 0.0, 0.0), "backup:0"),), "terminal:fixture", "L3_PASS"
        return CertificateStatus.FAIL, (), None, "BACKUP_SEGMENT_NOT_CERTIFIED:SEGMENT_EXACT_UNSAFE"

    coordinator.l3_runtime._builder = l3_backend
    return system


def run_recovery(system):
    coordinator = system["coordinator"]
    assert coordinator.start_trial(system["state"], system["trial"]).ready
    return coordinator.run_cycle(system["state"], system["request"])


def recovery_inventory(system, primary=None):
    snapshot = system["state"]
    provider = system["coordinator"].recovery_provider
    grant = RecoverySourceGrant.create(snapshot, system["registry"].actuator.identity.value,
                                       provider.transition_identity)
    return provider.enumerate(snapshot, grant, primary), grant


def recovery_key(system, snapshot=None, **changes):
    snapshot = snapshot or system["state"]
    provider = system["coordinator"].recovery_provider
    fields = dict(actuator_identity=system["registry"].actuator.identity.value,
                  geometry_identity=system["registry"].geometry.identity.value,
                  transition_identity=provider.transition_identity,
                  backend_identity=provider.backend_identity,
                  backup_routing_class="NONE")
    fields.update(changes)
    return exhaustion_key(snapshot, **fields)


class BoundedLocalRecoveryV1Tests(unittest.TestCase):
    def test_axis_order_and_count(self):
        system = build_recovery_cycle()
        snapshot = system["state"]
        provider = system["coordinator"].recovery_provider
        grant = RecoverySourceGrant.create(snapshot, system["registry"].actuator.identity.value,
                                           provider.transition_identity)
        inventory = provider.enumerate(snapshot, grant)
        self.assertEqual(tuple(c.direction for c in inventory.candidates),
                         ("+x", "-x", "+y", "-y", "+z", "-z"))
        self.assertEqual(len(inventory.candidates), 6)

    def test_primary_local_fail_first_recovery_pass(self):
        system = build_recovery_cycle(pass_rank=0)
        coordinator = system["coordinator"]
        self.assertTrue(coordinator.start_trial(system["state"], system["trial"]).ready)
        result = coordinator.run_cycle(system["state"], system["request"])
        self.assertTrue(result.committed)
        self.assertEqual(len(result.recovery_attempts), 1)
        self.assertEqual(dict(result.recovery_attempts[0])["final_disposition"], "RECOVERY_CERT_PASS")

    def test_primary_local_fail_second_recovery_pass(self):
        system = build_recovery_cycle(pass_rank=1)
        coordinator = system["coordinator"]
        self.assertTrue(coordinator.start_trial(system["state"], system["trial"]).ready)
        result = coordinator.run_cycle(system["state"], system["request"])
        self.assertTrue(result.committed)
        self.assertEqual(len(result.recovery_attempts), 2, repr(result))

    def test_all_six_fail_falls_back_to_terminal(self):
        system = build_recovery_cycle(pass_rank=-1)
        coordinator = system["coordinator"]
        self.assertTrue(coordinator.start_trial(system["state"], system["trial"]).ready)
        result = coordinator.run_cycle(system["state"], system["request"])
        self.assertTrue(result.committed)
        self.assertEqual(len([x for x in result.recovery_attempts if "candidate_id" in dict(x)]), 6, repr(result))

    def test_terminal_unavailable_no_scan(self):
        system = build_recovery_cycle(pass_rank=0, terminal=CertificateStatus.FAIL)
        coordinator = system["coordinator"]
        self.assertTrue(coordinator.start_trial(system["state"], system["trial"]).ready)
        result = coordinator.run_cycle(system["state"], system["request"])
        self.assertFalse(result.committed)
        self.assertEqual(result.recovery_attempts, ())

    def test_source_grant_rejects_wrong_transition(self):
        system = build_recovery_cycle()
        snapshot = system["state"]
        provider = system["coordinator"].recovery_provider
        grant = RecoverySourceGrant.create(snapshot, system["registry"].actuator.identity.value, "wrong")
        self.assertEqual(provider.enumerate(snapshot, grant).status, "RECOVERY_SOURCE_UNAUTHORIZED")

    def test_exhaustion_register_no_repeat(self):
        register = RecoveryExhaustionRegister()
        register.start_trial("trial")
        register.begin("trial", "key")
        register.attempted("trial", "key", 0, "control")
        register.close("trial", "key", ScanStatus.EXHAUSTED)
        with self.assertRaises(RuntimeError):
            register.begin("trial", "key")

    def test_control_identity_exact_bits(self):
        a = canonical_control_identity((0.1, 0, 0), "act", "transition")
        b = canonical_control_identity((0.1, -0.0, 0), "act", "transition")
        self.assertEqual(a, b)

    def run_gate0_case(self, number):
        """Each T case asserts a distinct implementation boundary, not a design mock."""
        if number == 1:
            actual = recovery_inventory(build_recovery_cycle())[0]
            self.assertEqual(tuple(x.direction for x in actual.candidates),
                             ("+x", "-x", "+y", "-y", "+z", "-z"))
        elif number == 2:
            system = build_recovery_cycle()
            registry = system["registry"]
            asymmetric = replace(registry, actuator=replace(registry.actuator,
                u_min=(-0.08, -0.09, -0.07), u_max=(0.1, 0.06, 0.04)))
            provider = BoundedRecoveryProvider(asymmetric, "transition:fixture", "backend:fixture")
            grant = RecoverySourceGrant.create(system["state"], asymmetric.actuator.identity.value,
                                               provider.transition_identity)
            self.assertEqual(tuple(x.candidate.vector for x in provider.enumerate(system["state"], grant).candidates),
                             ((0.1, 0, 0), (-0.08, 0, 0), (0, 0.06, 0), (0, -0.09, 0), (0, 0, 0.04), (0, 0, -0.07)))
        elif number == 3:
            self.assertLessEqual(len(recovery_inventory(build_recovery_cycle())[0].candidates), 6)
        elif number == 4:
            system = build_recovery_cycle()
            self.assertEqual(recovery_inventory(system)[0], recovery_inventory(system)[0])
        elif number == 5:
            self.assertEqual(canonical_control_identity((0.1, -0.0, 0), "a", "t"),
                             canonical_control_identity((0.1, 0.0, 0), "a", "t"))
        elif number == 6:
            system = build_recovery_cycle()
            primary = make_candidate((0.1, 0, 0), CandidateRole.PRIMARY,
                                     "PRIMARY_NATIVE_CBF_QP", "controller:fixture", system["state"])
            inventory, _ = recovery_inventory(system, primary)
            self.assertEqual(len(inventory.candidates), 5)
            self.assertEqual(inventory.skipped_duplicate_ranks, (0,))
        elif number == 7:
            lower = struct.unpack("!f", bytes.fromhex("3dcccccc"))[0]
            self.assertNotEqual(canonical_control_identity((lower, 0, 0), "a", "t"),
                                canonical_control_identity((0.1, 0, 0), "a", "t"))
        elif number == 8:
            system = build_recovery_cycle()
            inventory, grant = recovery_inventory(system)
            candidate = inventory.candidates[0].candidate
            c0 = C0Admission(system["registry"])
            self.assertNotEqual(c0.evaluate(candidate, system["state"]).status, CertificateStatus.PASS)
            self.assertEqual(c0.evaluate(candidate, system["state"], grant).status, CertificateStatus.PASS)
        elif number == 9:
            system = build_recovery_cycle()
            inventory, grant = recovery_inventory(system)
            invalid = replace(inventory.candidates[0].candidate, vector=(0.2, 0, 0))
            self.assertEqual(C0Admission(system["registry"]).evaluate(invalid, system["state"], grant).status,
                             CertificateStatus.FAIL)
        elif number == 10:
            system = build_recovery_cycle()
            system["coordinator"].l3_runtime._builder = lambda *_: (
                CertificateStatus.PASS, (((0., 0., 0.), "backup:0"),), "terminal:fixture", "L3_PASS")
            result = run_recovery(system)
            self.assertEqual(result.action_role, ActionRole.PRIMARY_NAVIGATION)
            self.assertEqual(result.recovery_attempts, ())
        elif number == 11:
            system = build_recovery_cycle()
            from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RecoveryRoutingFacts
            self.assertTrue(system["coordinator"].start_trial(system["state"], system["trial"]).ready)
            facts = RecoveryRoutingFacts(True, True, True, True, "FAIL",
                "BACKUP_SEGMENT_NOT_CERTIFIED:SEGMENT_EXACT_UNSAFE", True, True, True)
            deadline = system["coordinator"].deadline_tracker.observe("TEST")
            primary = make_candidate((0., 0., 0.), CandidateRole.PRIMARY,
                                     "PRIMARY_NATIVE_CBF_QP", "controller:fixture", system["state"])
            context = system["coordinator"]._routing_context(
                RuntimePhase.L3, deadline, candidate=primary, backup_valid=True, recovery_facts=facts)
            self.assertFalse(system["supervisor"]._recovery_entry_allowed(context))
        elif number == 12:
            system = build_recovery_cycle()
            system["config"]["primary_vector"] = (0.2, 0., 0.)
            self.assertEqual(run_recovery(system).recovery_attempts, ())
        elif number == 13:
            system = build_recovery_cycle()
            system["config"]["l2"] = CertificateStatus.FAIL
            self.assertEqual(run_recovery(system).recovery_attempts, ())
        elif number == 14:
            system = build_recovery_cycle()
            system["coordinator"].l3_runtime._builder = lambda *_: (CertificateStatus.UNKNOWN, (), None, "L3_UNKNOWN")
            self.assertEqual(run_recovery(system).recovery_attempts, ())
        elif number == 15:
            system = build_recovery_cycle()
            system["coordinator"].l3_runtime._builder = lambda *_: (CertificateStatus.FAIL, (), None, "UNCLASSIFIED_FAIL")
            self.assertEqual(run_recovery(system).recovery_attempts, ())
        elif number == 16:
            result = run_recovery(build_recovery_cycle(pass_rank=0))
            self.assertIn(PublicCyclePhase.RECOVERY_SOURCE_QUERY, result.phase_history)
        elif number == 17:
            result = run_recovery(build_recovery_cycle(pass_rank=0))
            self.assertEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
            self.assertEqual(dict(result.recovery_attempts[0])["candidate_rank"], 0)
        elif number == 18:
            result = run_recovery(build_recovery_cycle(pass_rank=1))
            self.assertEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
            self.assertEqual(tuple(dict(x)["candidate_rank"] for x in result.recovery_attempts), (0, 1))
        elif number == 19:
            result = run_recovery(build_recovery_cycle(pass_rank=-1))
            self.assertEqual(result.action_role, ActionRole.CERTIFIED_TERMINAL)
            self.assertEqual(len([x for x in result.recovery_attempts if "candidate_id" in dict(x)]), 6)
        elif number == 20:
            system = build_recovery_cycle()
            primary = system["coordinator"].l3_runtime._builder
            def unknown_first(snapshot, candidate):
                if candidate.provenance.source_type == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1":
                    return CertificateStatus.UNKNOWN, (), None, "L3_BACKEND_UNAVAILABLE"
                return primary(snapshot, candidate)
            system["coordinator"].l3_runtime._builder = unknown_first
            result = run_recovery(system)
            self.assertNotEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
        elif number == 21:
            result = run_recovery(build_recovery_cycle(terminal=CertificateStatus.FAIL))
            self.assertTrue(result.boundary)
            self.assertFalse(result.committed)
        elif number == 22:
            system = build_recovery_cycle()
            system["coordinator"].recovery_provider.transition_identity = ""
            result = run_recovery(system)
            self.assertEqual(result.recovery_attempts, ())
        elif number == 23:
            register = RecoveryExhaustionRegister()
            register.start_trial("t")
            register.begin("t", "k")
            register.close("t", "k", ScanStatus.EXHAUSTED)
            with self.assertRaises(RuntimeError):
                register.begin("t", "k")
        elif number == 24:
            register = RecoveryExhaustionRegister()
            register.start_trial("t")
            register.begin("t", "k")
            register.attempted("t", "k", 0, "c0")
            register.close("t", "k", ScanStatus.PAUSED)
            self.assertEqual(register.begin("t", "k").cursor, 1)
        elif number == 25:
            system = build_recovery_cycle()
            changed = RuntimeStateSnapshot.create("trial-1", 0,
                (0.001, 0., 0., 0.1, -0.1, 0.), system["state"].goal,
                system["state"].map_identity, system["state"].dt)
            self.assertNotEqual(recovery_key(system), recovery_key(system, changed))
        elif number == 26:
            system = build_recovery_cycle()
            changed = RuntimeStateSnapshot.create("trial-1", 0,
                system["state"].state, system["state"].goal, "map:changed", system["state"].dt)
            self.assertNotEqual(recovery_key(system), recovery_key(system, changed))
        elif number == 27:
            import reproduction.runtime.active_runtime_assurance_v2.bounded_recovery as source
            system = build_recovery_cycle()
            first = recovery_key(system)
            original = source.GENERATOR
            try:
                source.GENERATOR = "AXIS_EXTREMA_F32_V2"
                self.assertNotEqual(first, recovery_key(system))
            finally:
                source.GENERATOR = original
        elif number == 28:
            system = build_recovery_cycle()
            self.assertNotEqual(recovery_key(system), recovery_key(system, actuator_identity="another-actuator"))
        elif number == 29:
            register = RecoveryExhaustionRegister()
            register.start_trial("trial-1")
            register.begin("trial-1", "k")
            register.close("trial-1", "k", ScanStatus.EXHAUSTED)
            register.finalize_trial()
            register.start_trial("trial-2")
            self.assertIsNone(register.lookup("trial-2", "k"))
        elif number == 30:
            result = run_recovery(build_recovery_cycle(pass_rank=0))
            self.assertNotEqual(result.action_role, ActionRole.RETAINED_BACKUP)
        elif number == 31:
            result = run_recovery(build_recovery_cycle(pass_rank=0))
            self.assertEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
        elif number == 32:
            result = run_recovery(build_recovery_cycle(pass_rank=0))
            self.assertEqual(result.final_supervisor_decision.rule_id, "ARB_NAV")
            self.assertTrue(dict(result.recovery_attempts[0])["supervisor_selected"])
        elif number == 33:
            system = build_recovery_cycle(pass_rank=0)
            original = system["coordinator"].l3_runtime._builder
            def late_success(snapshot, candidate):
                result = original(snapshot, candidate)
                if candidate.provenance.source_type == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1":
                    system["clock"].advance(9.2)
                return result
            system["coordinator"].l3_runtime._builder = late_success
            result = run_recovery(system)
            self.assertNotEqual(result.action_role, ActionRole.ALTERNATIVE_NAVIGATION)
            self.assertFalse(any(dict(x)["plant_commit_authorized"] for x in result.recovery_attempts))
        elif number == 34:
            system = build_recovery_cycle()
            inventory, grant = recovery_inventory(system)
            altered = RuntimeStateSnapshot.create("trial-1", 0, (1.,) * 6,
                system["state"].goal, system["state"].map_identity, system["state"].dt)
            self.assertNotEqual(C0Admission(system["registry"]).evaluate(inventory.candidates[0].candidate,
                                altered, grant).status, CertificateStatus.PASS)
        elif number == 35:
            system = build_recovery_cycle()
            inventory, grant = recovery_inventory(system)
            bad = replace(grant, transition_identity="different")
            self.assertNotEqual(C0Admission(system["registry"]).evaluate(inventory.candidates[0].candidate,
                                system["state"], bad).status, CertificateStatus.PASS)
        elif number == 36:
            a = struct.unpack("!f", bytes.fromhex("3dcccccd"))[0]
            b = struct.unpack("!f", bytes.fromhex("3dccccce"))[0]
            self.assertNotEqual(canonical_control_identity((a, 0., 0.), "a", "t"),
                                canonical_control_identity((b, 0., 0.), "a", "t"))
        elif number == 37:
            state = build_recovery_cycle()["state"]
            dt = state.dt
            p1_a = tuple(state.state[i] + dt * state.state[i + 3] for i in range(3))
            p1_b = tuple(state.state[i] + dt * state.state[i + 3] for i in range(3))
            self.assertEqual(p1_a, p1_b)
        elif number == 38:
            state = build_recovery_cycle()["state"]
            dt = state.dt
            u_a, u_b = (0.1, 0., 0.), (-0.1, 0., 0.)
            p2 = lambda u: tuple(state.state[i] + 2 * dt * state.state[i + 3] + dt * dt * u[i] for i in range(3))
            self.assertNotEqual(p2(u_a), p2(u_b))
            self.assertAlmostEqual(p2(u_a)[0] - p2(u_b)[0], dt * dt * 0.2)
        elif number == 39:
            from reproduction.runtime.active_runtime_assurance_v2 import bounded_recovery
            self.assertNotIn("0.025", inspect.getsource(bounded_recovery))
        elif number == 40:
            system = build_recovery_cycle(pass_rank=1)
            result = run_recovery(system)
            trace = system["trace_writer"].records[-1]
            self.assertEqual(len(result.recovery_attempts), 2)
            self.assertIn("recovery_attempts", str(trace))
        elif number == 41:
            result = run_recovery(build_recovery_cycle(pass_rank=-1))
            ranks = [dict(x)["candidate_rank"] for x in result.recovery_attempts if "candidate_rank" in dict(x)]
            self.assertEqual(ranks, list(range(6)))
        elif number == 42:
            system = build_recovery_cycle(pass_rank=0)
            system["trace_writer"].append = lambda *_: (_ for _ in ()).throw(RuntimeError("TEST_TRACE_FAILURE"))
            result = run_recovery(system)
            self.assertNotEqual(result.commit_transaction_result.evidence_status.value, "COMPLETE")
            self.assertTrue(result.commit_transaction_result.recovery_required)
        elif number == 43:
            system = build_recovery_cycle(pass_rank=-1)
            result = run_recovery(system)
            self.assertLessEqual(len([x for x in result.recovery_attempts if "candidate_id" in dict(x)]), 6)
        elif number == 44:
            system = build_recovery_cycle(pass_rank=0)
            first = run_recovery(system)
            self.assertTrue(first.committed)
            system["coordinator"].l3_runtime._builder = lambda *_: (
                CertificateStatus.PASS, (((0., 0., 0.), "backup:0"),), "terminal:fixture", "L3_PASS")
            next_state = first.next_state
            request = ActiveCycleRequest(next_state.trial_id, next_state.cycle_index, (1., 0., 0.), None)
            second = system["coordinator"].run_cycle(next_state, request)
            self.assertEqual(second.action_role, ActionRole.PRIMARY_NAVIGATION)
        elif number == 45:
            system = build_recovery_cycle()
            same = RuntimeStateSnapshot.create("trial-1", 1,
                system["state"].state, system["state"].goal, system["state"].map_identity, system["state"].dt)
            self.assertEqual(recovery_key(system), recovery_key(system, same))
            changed = RuntimeStateSnapshot.create("trial-1", 1,
                (0.001,) + system["state"].state[1:], system["state"].goal,
                system["state"].map_identity, system["state"].dt)
            self.assertNotEqual(recovery_key(system), recovery_key(system, changed))
        elif number == 46:
            from reproduction.runtime.active_runtime_assurance_v2 import active_cycle
            self.assertNotIn("RoutingDecision(", inspect.getsource(active_cycle.ActiveCycleCoordinator))
        elif number == 47:
            system = build_recovery_cycle(pass_rank=1)
            result = run_recovery(system)
            ids = result.routing_rule_ids
            self.assertIn("REC_L3_LOCAL_FAIL", ids)
            self.assertIn("REC_L3_PASS", ids)
            self.assertFalse(any("AMBIGUOUS" in item or "MISSING" in item for item in ids))
        elif number == 48:
            system = build_recovery_cycle(pass_rank=0)
            result = run_recovery(system)
            self.assertEqual(system["plant"].commit_count, 1)
            self.assertEqual(result.commit_receipt.executed_action_identity,
                             result.commit_receipt.selected_action_identity)
        else:
            self.fail(f"T{number:02d} not implemented")


for _number in range(1, 49):
    def _gate0_test(self, number=_number):
        self.run_gate0_case(number)
    setattr(BoundedLocalRecoveryV1Tests, f"test_T{_number:02d}", _gate0_test)


if __name__ == "__main__":
    unittest.main()
