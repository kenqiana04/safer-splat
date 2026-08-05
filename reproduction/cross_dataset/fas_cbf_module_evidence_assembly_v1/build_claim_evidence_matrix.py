#!/usr/bin/env python3
"""Audit every candidate claim against frozen, non-pooled evidence."""
from __future__ import annotations

from evidence_common import TASK, write_csv, write_json, write_text

CLAIMS = [
    {"claim_id": "C1", "claim": "Start-Safe can identify and repair local unsafe/near-unsafe initial states.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E05,E06,E07,E03", "limits": "Natural, synthetic, and GT-derived contexts have different denominators.", "paper_safe_wording": "In the reported frozen contexts, verified Start-Safe repair identified and repaired local unsafe/near-unsafe starts.", "prohibited_stronger_wording": "Start-Safe universally repairs all unsafe starts."},
    {"claim_id": "C2", "claim": "Start-Safe reduces failures caused by initial conditions relative to no repair.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E04,E05", "limits": "Original and post-repair navigation are deliberately separate outcomes.", "paper_safe_wording": "Post-repair flight100 is collision-free in the reported repair-needed cases while original trial57 remains preserved.", "prohibited_stronger_wording": "Start-Safe proves original-benchmark superiority."},
    {"claim_id": "C3", "claim": "Feasibility/Risk-Aware constraint handling lowers active constraints and some runtime.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E08,E09,E10,E01,E02", "limits": "Risk-Aware V1 and Feasibility-Aware labels are not interchangeable; ETH3D designated H2 did not enter QP.", "paper_safe_wording": "Risk-Aware V1 bestD provides configuration-specific formal efficiency evidence in Stonehenge and flight.", "prohibited_stronger_wording": "All FAS feasibility modules are universally faster or safer."},
    {"claim_id": "C4", "claim": "DT Verification detects sampled/horizon margin risk not explicit in pointwise CBF reporting.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E11,E17,E02", "limits": "Margin-risk detection is distinct from collision and from closed-loop avoidance.", "paper_safe_wording": "The frozen DT audits detect sampled/horizon margin-risk precursors under their stated dynamics and margins.", "prohibited_stronger_wording": "DT detection proves universal collision reduction."},
    {"claim_id": "C5", "claim": "DT Verification universally reduces real collision.", "status": "PROHIBITED", "supporting_evidence_ids": "", "limits": "No same-map, activated, paired collision-outcome evidence supports this generalization.", "paper_safe_wording": "No global collision-reduction claim is made for DT Verification.", "prohibited_stronger_wording": "DT Verification has proven universal collision avoidance."},
    {"claim_id": "C6", "claim": "Predictive Recovery eliminates observed H-step margin violations under frozen configurations.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E13,E14,E18", "limits": "Dense-flight H3/H2 and bounded TUM intervention use different contracts; TUM uses an overlap proxy.", "paper_safe_wording": "In the stated dense-flight and bounded TUM configurations, predictive recovery removed the reported executed risk events.", "prohibited_stronger_wording": "Predictive Recovery universally resolves all future safety risks."},
    {"claim_id": "C7", "claim": "Predictive Recovery universally improves completion or safety relative to SAFER.", "status": "PROHIBITED", "supporting_evidence_ids": "", "limits": "No common fully activated registry establishes a general paired superiority effect.", "paper_safe_wording": "No general completion or safety-superiority claim is made.", "prohibited_stronger_wording": "Predictive Recovery is universally superior to SAFER."},
    {"claim_id": "C8", "claim": "HCE reduces activated recovery runtime while preserving existing recovery outcomes.", "status": "CONFIGURATION_SPECIFIC", "supporting_evidence_ids": "E15,E16", "limits": "Held-out activated cohort only; Stage-B failures are retained.", "paper_safe_wording": "HCE reduced activated median runtime from about 8.000 s to 1.643 s in its frozen held-out activated cohort without converting Stage-B failures.", "prohibited_stronger_wording": "HCE adds recovery capability or reduces runtime universally."},
    {"claim_id": "C9", "claim": "Full FAS-CBF is superior to SAFER on all maps.", "status": "PROHIBITED", "supporting_evidence_ids": "", "limits": "Replica saturates and ETH3D lacks an activated H3 paired cohort.", "paper_safe_wording": "Full-stack superiority is not established.", "prohibited_stronger_wording": "Full FAS-CBF is globally superior to SAFER."},
    {"claim_id": "C10", "claim": "Full FAS-CBF is a planner-agnostic safety assurance layer.", "status": "PARTIALLY_SUPPORTED", "supporting_evidence_ids": "E01,E03,E05,E11,E13,E17", "limits": "Architecture-level framing is broader than the configuration-specific empirical evidence.", "paper_safe_wording": "FAS-CBF can be framed as a modular safety-assurance architecture with module-specific empirical support.", "prohibited_stronger_wording": "It is empirically proven planner-agnostic across planners, maps, and dynamics."},
    {"claim_id": "C11", "claim": "ETH3D establishes learned-map controller viability and external portability.", "status": "PARTIALLY_SUPPORTED", "supporting_evidence_ids": "E01,E02", "limits": "One learned external 3DGS map; full-stack stress activation is structurally limited.", "paper_safe_wording": "ETH3D provides a learned-3DGS external viability and portability carrier with an explicit activation limit.", "prohibited_stronger_wording": "ETH3D proves learned-map deployment safety."},
    {"claim_id": "C12", "claim": "ETH3D establishes learned-map deployment safety.", "status": "PROHIBITED", "supporting_evidence_ids": "", "limits": "Minimum controller viability is not deployment certification and no activated full-stack paired outcome exists.", "paper_safe_wording": "No learned-map deployment-safety claim is made.", "prohibited_stronger_wording": "The ETH3D map is deployment-certified."}
]


def main() -> int:
    fields = list(CLAIMS[0])
    write_csv(TASK / "claim_audit/claim_evidence_matrix.csv", CLAIMS, fields)
    write_json(TASK / "claim_audit/claim_evidence_matrix.json", {"claims": CLAIMS})
    dt = """# DT Evidence Taxonomy

| Category | Frozen evidence | Claim boundary |
|---|---|---|
| POINTWISE_ENDPOINT_RISK | ETH3D strict endpoint-unsafe/QP-feasible count is 0 | Absence under one frozen contract is not DT invalidity. |
| CONTINUOUS_SEGMENT_RISK | ETH3D has 2 endpoint-safe/segment-unsafe states | Segment risk is not endpoint collision. |
| MARGIN_RISK | Dense-flight H1/H2/H3: 463/488/519; ETH3D: 4394 shadow margin states | Margin violation is not collision. |
| HSTEP_PREDICTED_RISK | TUM step-772 precursor; dense-flight H-step audit | Prediction alone is not avoidance. |
| EXECUTED_COLLISION_OR_OVERLAP | Original trial57 collision; TUM GSplat overlap proxy | Mesh collision and overlap proxy remain distinct. |
| INTERVENTION_AVOIDANCE | Bounded strict-trigger TUM V4-C intervention; dense-flight executed H-step margin reduction | Configuration-specific mechanism evidence, not global superiority. |
"""
    write_text(TASK / "claim_audit/DT_EVIDENCE_TAXONOMY.md", dt)
    safe = "# Paper-Safe Claims\n\n" + "\n".join(f"- **{row['claim_id']} ({row['status']})**: {row['paper_safe_wording']}" for row in CLAIMS if row["status"] != "PROHIBITED")
    prohibited = "# Prohibited Claims\n\n" + "\n".join(f"- **{row['claim_id']}**: {row['prohibited_stronger_wording']}" for row in CLAIMS)
    write_text(TASK / "claim_audit/paper_safe_claims.md", safe)
    write_text(TASK / "claim_audit/prohibited_claims.md", prohibited)
    print("PASS_CLAIM_EVIDENCE_MATRIX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
