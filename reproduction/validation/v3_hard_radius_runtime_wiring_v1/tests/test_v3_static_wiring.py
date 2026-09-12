from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import build_v3_stack, load_frozen_v2_build_stack


REPO_ROOT = Path(__file__).resolve().parents[4]
V2_RUNNER = REPO_ROOT / "reproduction" / "smoke" / "active_runtime_smoke_v2" / "run_active_runtime_smoke_v2.py"


def fake_v2_build_stack(checkout, output_dir, trial_id, config, map_identity):
    registry = AuthorityRegistry.frozen(map_identity, "dt:test", "deadline:test")
    effective_radius = float(config["certification"]["certification_effective_radius"])
    rho_seg = float(config["certification"]["rho_seg"])
    map_adapter = SimpleNamespace(effective_radius=effective_radius)
    segment_backend = SimpleNamespace(provider=map_adapter)

    def full_query(*args):
        return map_adapter, effective_radius

    def segment_query(*args):
        return segment_backend, effective_radius, rho_seg

    current_adapter = SimpleNamespace(barrier_adapter=map_adapter)
    swept = SimpleNamespace(backend=segment_backend, effective_radius=effective_radius, rho_seg=rho_seg)
    terminal_certifier = SimpleNamespace(current_adapter=current_adapter, segment_certifier=swept)
    backup_certifier = SimpleNamespace(segment_certifier=swept, terminal_certifier=terminal_certifier)

    def l3_witness(*args):
        return backup_certifier

    def terminal_backend(*args):
        return terminal_certifier

    coordinator = SimpleNamespace(
        start_admission=SimpleNamespace(_full_query=full_query),
        l1_runtime=SimpleNamespace(_backend=segment_query),
        l2_runtime=SimpleNamespace(_backend=segment_query),
        l3_runtime=SimpleNamespace(_builder=l3_witness),
        terminal_runtime=SimpleNamespace(_backend=terminal_backend),
    )
    return {"registry": registry, "coordinator": coordinator}


class V3StaticWiringTests(unittest.TestCase):
    def test_frozen_v2_composition_has_required_authority_edges(self):
        source = V2_RUNNER.read_text(encoding="utf-8")
        required = (
            "effective_radius = float(cert_cfg[\"certification_effective_radius\"])",
            "SourceGaussianBarrierAdapter(query_bridge, map_identity, effective_radius",
            "SweptSegmentCertifier(normative_dynamics, segment_backend, effective_radius, cert_cfg[\"rho_seg\"])",
            "TerminalCertifier(terminal_set, current_adapter, swept)",
            "BackupCertifier(normative_dynamics, swept, terminal_certifier, braking)",
            "supervisor = Supervisor(",
            "plant = PlantCommitAdapter(",
            "runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON",
            "coordinator = ActiveCycleCoordinator(",
        )
        for edge in required:
            self.assertIn(edge, source)
        self.assertTrue(callable(load_frozen_v2_build_stack))

    def test_factory_injects_v3_registry_and_restores_v2_default(self):
        base = {
            "controller": {"controller_radius": 0.015},
            "certification": {"certification_effective_radius": 0.025, "rho_seg": 0.0},
        }
        stack = build_v3_stack(
            REPO_ROOT,
            REPO_ROOT,
            0,
            base,
            "map:test",
            v2_build_stack=fake_v2_build_stack,
        )
        self.assertEqual(stack["registry"].geometry.certification_effective_radius_m, 0.015)
        self.assertEqual(stack["v3_wiring_audit"]["status"], "PASS")
        self.assertTrue(all(stack["v3_wiring_audit"]["checks"].values()))
        restored = AuthorityRegistry.frozen("map:test", "dt:test")
        self.assertEqual(restored.geometry.certification_effective_radius_m, 0.025)

    def test_factory_does_not_mutate_base_config(self):
        base = {
            "controller": {"controller_radius": 0.015},
            "certification": {"certification_effective_radius": 0.025, "rho_seg": 0.0},
        }
        original = {
            "controller": {"controller_radius": 0.015},
            "certification": {"certification_effective_radius": 0.025, "rho_seg": 0.0},
        }
        build_v3_stack(REPO_ROOT, REPO_ROOT, 0, base, "map:test", v2_build_stack=fake_v2_build_stack)
        self.assertEqual(base, original)


if __name__ == "__main__":
    unittest.main()
