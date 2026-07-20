"""Runtime checks for the read-only V1R6 SAFER adapter.

Run only with V1R6_CONFIG and V1R6_CHECKPOINT pointing at the frozen server
assets.  The test never writes to either input path.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

import torch

from tum_v1r6_safer_checkpoint_adapter import (
    deterministic_sample_fingerprint,
    extract_safer_gaussians,
    verify_v1r6_identity,
)


CONFIG = Path(os.environ["V1R6_CONFIG"])
CHECKPOINT = Path(os.environ["V1R6_CHECKPOINT"])


class TestTumV1R6SaferCheckpointAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_mtimes = (CONFIG.stat().st_mtime_ns, CHECKPOINT.stat().st_mtime_ns)
        cls.identity = verify_v1r6_identity(CONFIG, CHECKPOINT)
        cls.gaussians = extract_safer_gaussians(CONFIG, CHECKPOINT)

    def test_frozen_identity(self) -> None:
        self.assertEqual(self.identity["checkpoint_sha256"], "4941bf1faba1aed31949ee4114898c0eec33ff1a46b7bcadad6d06f5f647ae6b")
        self.assertEqual(self.identity["config_sha256"], "c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe")

    def test_geometry_schema_and_finiteness(self) -> None:
        g = self.gaussians
        self.assertGreater(g.means_world.shape[0], 0)
        self.assertEqual(tuple(g.means_world.shape[1:]), (3,))
        self.assertEqual(tuple(g.scales_world.shape), tuple(g.means_world.shape))
        self.assertEqual(tuple(g.quaternions_wxyz.shape), (g.means_world.shape[0], 4))
        self.assertEqual(tuple(g.covariances_world.shape), (g.means_world.shape[0], 3, 3))
        self.assertTrue(torch.isfinite(g.means_world).all())
        self.assertTrue(torch.isfinite(g.scales_world).all())
        self.assertTrue(torch.all(g.scales_world > 0))
        self.assertTrue(torch.isfinite(g.quaternions_wxyz).all())
        self.assertTrue(torch.allclose(torch.linalg.vector_norm(g.quaternions_wxyz, dim=-1), torch.ones(g.means_world.shape[0], device=g.means_world.device), atol=1e-5))
        self.assertTrue(torch.all((g.opacities >= 0) & (g.opacities <= 1)))
        self.assertTrue(torch.allclose(g.covariances_world, g.covariances_world.transpose(-1, -2), atol=1e-5))
        self.assertTrue(torch.all(torch.linalg.eigvalsh(g.covariances_world) >= -1e-6))

    def test_read_only_sources_unchanged(self) -> None:
        self.assertEqual(self.source_mtimes, (CONFIG.stat().st_mtime_ns, CHECKPOINT.stat().st_mtime_ns))

    def test_repeatable_prefix_fingerprint(self) -> None:
        self.assertEqual(deterministic_sample_fingerprint(self.gaussians), deterministic_sample_fingerprint(self.gaussians))


if __name__ == "__main__":
    unittest.main(verbosity=2)
