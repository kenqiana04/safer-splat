"""Read-only Nerfstudio Splatfacto V1R6 to SAFER Gaussian schema adapter.

This module deliberately contains no training, filtering, checkpoint writing, or
navigation code.  It uses Nerfstudio's official ``eval_setup`` loader and uses
the same parameter activations and covariance implementation as
``splat/gsplat_utils.py``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from ellipsoids.covariance_utils import compute_cov
from nerfstudio.utils.eval_utils import eval_setup


EXPECTED_CHECKPOINT_SHA256 = "4941bf1faba1aed31949ee4114898c0eec33ff1a46b7bcadad6d06f5f647ae6b"
EXPECTED_CONFIG_SHA256 = "c9a103c38483f76aed4701489084347566c2437719ae54ea962017469c708cfe"


def sha256_file(path: Path) -> str:
    """Return the raw-byte SHA-256 of a read-only input file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_v1r6_identity(config_path: Path, checkpoint_path: Path) -> dict[str, Any]:
    """Fail closed if either frozen V1R6 source identity differs."""
    config_sha256 = sha256_file(config_path)
    checkpoint_sha256 = sha256_file(checkpoint_path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise RuntimeError(f"V1R6_CONFIG_SHA256_MISMATCH:{config_sha256}")
    if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
        raise RuntimeError(f"V1R6_CHECKPOINT_SHA256_MISMATCH:{checkpoint_sha256}")
    return {
        "config_path": str(config_path),
        "config_sha256": config_sha256,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_sha256,
    }


@dataclass(frozen=True)
class SaferGaussianMap:
    """Schema consumed by the existing SAFER Gaussian/ellipsoid query layer."""

    means_world: torch.Tensor
    scales_world: torch.Tensor
    quaternions_wxyz: torch.Tensor
    opacities: torch.Tensor
    covariances_world: torch.Tensor
    features_dc: torch.Tensor
    features_rest: torch.Tensor
    metadata: dict[str, Any]


def _clone_detached(tensor: torch.Tensor) -> torch.Tensor:
    return tensor.detach().clone()


def extract_safer_gaussians(config_path: Path, checkpoint_path: Path) -> SaferGaussianMap:
    """Load V1R6 through Nerfstudio and expose its unfiltered Gaussian map.

    The checkpoint path is identity-checked before loading.  Nerfstudio resolves
    the configured final checkpoint via the frozen config; the recorded step is
    independently checked from the checkpoint payload by the audit runner.
    """
    identity = verify_v1r6_identity(config_path, checkpoint_path)
    config, pipeline, _, step = eval_setup(config_path, test_mode="inference")
    if int(step) != 29999:
        raise RuntimeError(f"V1R6_LOADED_STEP_MISMATCH:{step}")
    pipeline.eval()
    model = pipeline.model
    model.eval()
    required = ("means", "scales", "quats", "opacities", "features_dc", "features_rest")
    missing = [name for name in required if not hasattr(model, name)]
    if missing:
        raise RuntimeError(f"SPLATFACTO_GAUSSIAN_ATTRIBUTES_MISSING:{','.join(missing)}")
    with torch.no_grad():
        means = _clone_detached(model.means)
        raw_scales = _clone_detached(model.scales)
        scales = torch.exp(raw_scales)
        raw_quaternions = _clone_detached(model.quats)
        quaternion_norms = torch.linalg.vector_norm(raw_quaternions, dim=-1, keepdim=True)
        if bool(torch.any(quaternion_norms <= 0)):
            raise RuntimeError("SPLATFACTO_ZERO_NORM_QUATERNION")
        quaternions = raw_quaternions / quaternion_norms
        raw_opacities = _clone_detached(model.opacities)
        opacities = torch.sigmoid(raw_opacities)
        covariances = compute_cov(quaternions, scales)
        features_dc = _clone_detached(model.features_dc)
        features_rest = _clone_detached(model.features_rest)
    metadata = {
        **identity,
        "loaded_step": int(step),
        "pipeline_class": f"{type(pipeline).__module__}.{type(pipeline).__name__}",
        "model_class": f"{type(model).__module__}.{type(model).__name__}",
        "config_class": f"{type(config).__module__}.{type(config).__name__}",
        "coordinate_frame": "Nerfstudio world coordinates; no axis conversion applied",
        "units": "raw frozen V1R6 world units; metric interpretation is audited separately",
        "quaternion_order": "wxyz, normalized before covariance construction",
        "scale_semantics": "exp(raw Splatfacto log-scales), matching splat/gsplat_utils.py",
        "opacity_semantics": "sigmoid(raw Splatfacto opacities), matching splat/gsplat_utils.py",
        "covariance_semantics": "R @ diag(scales)^2 @ R.T via ellipsoids.covariance_utils.compute_cov",
        "filtering": "none; all extracted Gaussians retained",
        "device": str(means.device),
        "dtype": str(means.dtype),
        "gaussian_count": int(means.shape[0]),
    }
    return SaferGaussianMap(means, scales, quaternions, opacities, covariances, features_dc, features_rest, metadata)


def deterministic_sample_fingerprint(gaussians: SaferGaussianMap, count: int = 1024) -> str:
    """Hash a fixed prefix of canonical tensors for cross-process determinism."""
    limit = min(count, gaussians.means_world.shape[0])
    digest = hashlib.sha256()
    for tensor in (
        gaussians.means_world[:limit],
        gaussians.scales_world[:limit],
        gaussians.quaternions_wxyz[:limit],
        gaussians.opacities[:limit],
        gaussians.covariances_world[:limit],
    ):
        canonical = tensor.detach().to(device="cpu", dtype=torch.float32).contiguous().numpy().tobytes()
        digest.update(canonical)
    return digest.hexdigest()


def schema_summary(gaussians: SaferGaussianMap) -> dict[str, Any]:
    """Return compact serializable schema evidence without serializing the map."""
    tensors = {
        "means_world": gaussians.means_world,
        "scales_world": gaussians.scales_world,
        "quaternions_wxyz": gaussians.quaternions_wxyz,
        "opacities": gaussians.opacities,
        "covariances_world": gaussians.covariances_world,
        "features_dc": gaussians.features_dc,
        "features_rest": gaussians.features_rest,
    }
    return {
        "schema": {name: {"shape": list(value.shape), "dtype": str(value.dtype), "device": str(value.device)} for name, value in tensors.items()},
        "metadata": gaussians.metadata,
        "deterministic_prefix_1024_sha256": deterministic_sample_fingerprint(gaussians),
    }


def main() -> None:
    import argparse
    import contextlib
    import sys

    parser = argparse.ArgumentParser(description="Read-only V1R6 Splatfacto-to-SAFER adapter")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    # Nerfstudio emits loader progress to stdout; keep the machine-readable
    # adapter summary clean and preserve loader diagnostics on stderr instead.
    with contextlib.redirect_stdout(sys.stderr):
        gaussians = extract_safer_gaussians(args.config, args.checkpoint)
    print(json.dumps(schema_summary(gaussians), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
