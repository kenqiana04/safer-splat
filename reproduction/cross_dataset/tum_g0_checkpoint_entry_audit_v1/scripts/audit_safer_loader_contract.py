#!/usr/bin/env python3
"""Extract only static source references for the official GSplat loader contract."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
source = REPO / "splat" / "gsplat_utils.py"
text = source.read_text(encoding="utf-8")
required = ["means", "rots", "scales", "colors", "opacities"]
data = {"loader_contract_status": "adapter_likely_required", "audit_mode": "static_source_only_no_loader_execution", "source_path": "splat/gsplat_utils.py", "source_readable": source.is_file(), "required_checkpoint_artifacts": ["Nerfstudio config path", "Nerfstudio model checkpoint under nerfstudio_models"], "required_gaussian_attributes": {"means": "N x 3", "rotations": "N x 4 quaternion", "scales": "N x 3", "colors": "N x 3 or SH-derived", "opacities": "N x 1"}, "coordinate_requirements": "loader consumes Gaussian means in the same metric world frame as query states", "metric_scale_requirements": "no unaccounted scene transform or pose normalization", "static_attribute_markers_found": {key: (key in text) for key in required}, "known_adapter_gaps": ["No TUM checkpoint exists", "actual Nerfstudio serialized attribute names/shapes are unverified", "scene transform and metric frame adaptation are unverified"], "core_modification_required": False, "recommended_allowed_adapter_location": "reproduction/ or work/ only, in a separately authorized task", "safer_loader_validated": False}
(ROOT / "safer_loader_contract_audit.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("safer_loader=static_only")
