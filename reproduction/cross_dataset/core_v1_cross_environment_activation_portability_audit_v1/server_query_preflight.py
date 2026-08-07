"""Read-only PR84 adapter and official-map finite-query preflight."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")
PROJECT = Path("/disk1/zlab/projects/safer-splat")
sys.path[:0] = [str(ROOT / "runtime_payload/pr84"), str(PROJECT)]

from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter  # noqa: E402
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend  # noqa: E402
from splat.gsplat_utils import GSplatLoader  # noqa: E402


SCENES = {
    "E5_STONEHENGE_SAFER": {
        "config": PROJECT / "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml",
        "snapshot": "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
        "position": [0.312, -0.03, 0.05],
    },
    "E6_FLIGHT_SAFER": {
        "config": PROJECT / "outputs/flight/splatfacto/2024-09-12_172434/config.yml",
        "snapshot": "8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6",
        "position": [0.4625, 0.01, -0.02],
    },
}


def tensor_sha(value: torch.Tensor) -> str:
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def main() -> None:
    os.chdir(PROJECT)
    records = {}
    for environment, config in SCENES.items():
        started = time.perf_counter()
        loader = GSplatLoader(config["config"], "cuda:0")
        means_before = tensor_sha(loader.means)
        def tensor_bridge(point, **kwargs):
            if not torch.is_tensor(point):
                point = torch.as_tensor(point, device="cuda:0", dtype=torch.float32)
            return loader.query_distance(point, **kwargs)
        adapter = SourceGaussianBarrierAdapter(tensor_bridge, config["snapshot"], .11, int(loader.means.shape[0]))
        adapter.segment_backend = ConservativeSignedDistanceIntervalBackend(adapter)
        query = adapter.query(torch.tensor(config["position"], device="cuda:0", dtype=torch.float32), config["snapshot"], "FULL")
        zero_segment = adapter.segment_backend.certify(np.asarray(config["position"]), np.asarray(config["position"]), config["snapshot"], config["snapshot"], .11)
        torch.cuda.synchronize()
        means_after = tensor_sha(loader.means)
        segment_typed = zero_segment.status.value in {"CERTIFIED_SAFE", "CERTIFIED_UNSAFE"}
        records[environment] = {
            "status": "PASS_PR84_COMPATIBLE_FINITE_QUERY" if query.status.value == "FINITE" and segment_typed and means_before == means_after else "QUERY_PREFLIGHT_FAILED",
            "query_status": query.status.value, "query_reason": query.reason_code, "h": query.h,
            "signed_distance": query.signed_distance, "active_gaussian_ids": list(query.active_gaussian_ids),
            "evaluated_gaussian_count": query.evaluated_gaussian_count,
            "segment_backend": zero_segment.method, "zero_segment_certified": zero_segment.certified,
            "zero_segment_status": zero_segment.status.value, "typed_safe_or_unsafe_result": segment_typed,
            "zero_segment_reason": zero_segment.reason_code, "means_sha256_before": means_before,
            "means_sha256_after": means_after, "map_mutation": means_before != means_after,
            "runtime_s": time.perf_counter() - started,
        }
        del adapter, loader
        torch.cuda.empty_cache()
    payload = {"status": "PASS_NONREPLICA_QUERY_PREFLIGHT" if all(value["status"].startswith("PASS") for value in records.values()) else "BLOCKED_NONREPLICA_QUERY_PREFLIGHT", "records": records, "map_mutation_count": 0}
    output = ROOT / "audits/nonreplica_query_preflight.json"
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
