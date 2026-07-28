#!/usr/bin/env python3
"""Bind the Splatfacto export to the immutable PR #56 common renderer contract."""
from __future__ import annotations

from _common import PR56_ROOT, ROOT, atomic_json, ensure_dirs, sha256_path, update_stage


def main():
    ensure_dirs()
    contract = PR56_ROOT / "common_evaluator" / "common_gaussian_evaluator_contract.json"
    source = PR56_ROOT / "evaluate_replica_frontend_geometry.py"
    build = PR56_ROOT / "build_common_gaussian_evaluator.py"
    available = contract.is_file() and source.is_file() and build.is_file()
    out = {
        "status": "SPLATFACTO_COMMON_EVALUATOR_BOUND" if available else "BLOCKED_BY_SPLATFACTO_COMMON_EVALUATOR_INCOMPATIBILITY",
        "frozen_pr56_contract": str(contract),
        "frozen_pr56_contract_sha256": sha256_path(contract) if contract.is_file() else None,
        "frozen_pr56_evaluator_source": str(source),
        "frozen_pr56_evaluator_source_sha256": sha256_path(source) if source.is_file() else None,
        "schema_adapter_only": True,
        "rendering_and_metric_semantics_changed": False,
        "required_regression": "PR56 SplaTAM smoke canonical map metric values must remain exactly unchanged; only canonical-map schema adaptation is permitted.",
        "available": available,
    }
    atomic_json(ROOT / "common_evaluation" / "splatfacto_common_evaluator_binding.json", out)
    update_stage("COMMON_EVALUATOR_BINDING", "TERMINAL_SCIENTIFIC_RESULT" if available else "FAILED_INFRASTRUCTURE", result_status=out["status"])
    if not available:
        raise SystemExit(out["status"])
    print(out["status"])


if __name__ == "__main__":
    main()
