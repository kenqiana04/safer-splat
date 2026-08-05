#!/usr/bin/env python3
"""Grade each module by evidence layer without collapsing claim boundaries."""
from __future__ import annotations

from evidence_common import TASK, write_csv, write_json, write_text

MODULES = [
    {"module_id": "M-A", "module": "Certified Start-Safe", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": True, "efficiency_supported": False, "detection_only": False, "shadow_only": False, "negative_ablation_supported": False, "structural_boundary_supported": False, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E04,E05,E06,E07,E03", "assessment": "Active natural repair, verified projection, and synthetic stress evidence; original/post-repair remain separate."},
    {"module_id": "M-B", "module": "Feasibility-Aware / constraint handling", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": True, "efficiency_supported": False, "detection_only": False, "shadow_only": True, "negative_ablation_supported": True, "structural_boundary_supported": True, "not_supported": False, "insufficient_evidence": True, "evidence_ids": "E01,E02,E10", "assessment": "ETH3D constraint reduction is real globally but designated H2 states stopped before entry; Adaptive V1 is forced-dominated."},
    {"module_id": "M-C", "module": "Risk-Aware V1 efficiency support", "implemented": True, "mechanism_supported": True, "paired_effect_supported": True, "configuration_specific_supported": True, "efficiency_supported": True, "detection_only": False, "shadow_only": False, "negative_ablation_supported": False, "structural_boundary_supported": False, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E08,E09", "assessment": "Formal Stonehenge and flight efficiency evidence, but no cross-scene safety superiority."},
    {"module_id": "M-D", "module": "Discrete-Time Verification", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": True, "efficiency_supported": False, "detection_only": True, "shadow_only": False, "negative_ablation_supported": True, "structural_boundary_supported": True, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E11,E12,E17,E02", "assessment": "Detects sampled/horizon margin risk and has precursor evidence; margin is not collision and ETH3D strict H3 stratum is unavailable."},
    {"module_id": "M-E", "module": "Predictive Recovery", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": True, "efficiency_supported": False, "detection_only": False, "shadow_only": False, "negative_ablation_supported": False, "structural_boundary_supported": True, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E13,E14,E16,E18,E03,E02", "assessment": "Active dense-flight recovery and bounded TUM intervention evidence; trial20 and ETH3D retain structural limits."},
    {"module_id": "M-F", "module": "HCE recovery efficiency", "implemented": True, "mechanism_supported": True, "paired_effect_supported": True, "configuration_specific_supported": True, "efficiency_supported": True, "detection_only": False, "shadow_only": False, "negative_ablation_supported": False, "structural_boundary_supported": True, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E15,E16", "assessment": "Held-out activated-cohort runtime reduction preserves rather than fixes Stage-B failures."},
    {"module_id": "M-G", "module": "Full FAS-CBF stack", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": False, "efficiency_supported": False, "detection_only": False, "shadow_only": False, "negative_ablation_supported": False, "structural_boundary_supported": True, "not_supported": True, "insufficient_evidence": True, "evidence_ids": "E01,E02,E03", "assessment": "Replica outcomes saturate and ETH3D lacks activated H3 paired cases; global superiority is unsupported."},
    {"module_id": "M-H", "module": "Structural boundary / recovery exhaustion", "implemented": True, "mechanism_supported": True, "paired_effect_supported": False, "configuration_specific_supported": True, "efficiency_supported": False, "detection_only": False, "shadow_only": True, "negative_ablation_supported": True, "structural_boundary_supported": True, "not_supported": False, "insufficient_evidence": False, "evidence_ids": "E02,E12,E16", "assessment": "Records retained impossibility/limit results without generalizing them beyond their frozen contracts."}
]


def main() -> int:
    fields = list(MODULES[0])
    write_csv(TASK / "module_matrices/module_evidence_matrix.csv", MODULES, fields)
    write_json(TASK / "module_matrices/module_evidence_matrix.json", {"modules": MODULES})
    narrative = "# Module Evidence Narrative\n\n" + "\n".join(f"- **{row['module_id']} {row['module']}** — {row['assessment']}" for row in MODULES)
    write_text(TASK / "module_matrices/module_evidence_narrative.md", narrative)
    print("PASS_MODULE_EVIDENCE_MATRIX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
