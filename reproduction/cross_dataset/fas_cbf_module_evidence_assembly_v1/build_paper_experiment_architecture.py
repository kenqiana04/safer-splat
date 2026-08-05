#!/usr/bin/env python3
"""Freeze a reviewer-facing experiment architecture without drafting a full paper."""
from __future__ import annotations

from evidence_common import TASK, write_json, write_text


def main() -> int:
    sections = [
        {"section": "E1 Baselines and map roles", "evidence": ["E01", "E02", "E03"], "message": "Separate official SAFER, Replica GT-derived, ETH3D learned-3DGS, and TUM learned-SLAM roles."},
        {"section": "E2 Certified Start-Safe", "evidence": ["E04", "E05", "E06", "E07", "E03"], "message": "Report natural eight repairs, synthetic 120 states, Replica static 30 states, and original/post-repair separation."},
        {"section": "E3 Constraint and efficiency", "evidence": ["E08", "E09", "E10", "E01", "E02"], "message": "Use Stonehenge and flight formal efficiency; retain forced-dominance and ETH3D semantic limits."},
        {"section": "E4 Discrete-Time Verification", "evidence": ["E11", "E12", "E17", "E02"], "message": "Show detection taxonomy, one-step negative ablation, TUM precursor, and ETH3D activation limit."},
        {"section": "E5 Predictive Recovery", "evidence": ["E13", "E14", "E15", "E16", "E18", "E03", "E02"], "message": "Show H3/H2, HCE, recovery exhaustion, bounded TUM intervention, Replica mechanism activation, and ETH3D opportunity evidence."},
        {"section": "E6 Full stack and external validity", "evidence": ["E03", "E01", "E02"], "message": "Report Replica saturation and ETH3D Case B/D; do not claim single-benchmark or global superiority."},
    ]
    write_json(TASK / "paper_architecture/paper_experiment_architecture.json", {"sections": sections})
    prose = "# Paper-Ready Experiment Architecture\n\n" + "\n".join(f"## {row['section']}\n\n{row['message']}\n\nEvidence: {', '.join(row['evidence'])}." for row in sections)
    prose += "\n\n## Reviewer-facing claim boundary\n\nThe paper should present a modular safety-assurance architecture with configuration-specific module evidence, not a globally superior Full FAS-CBF benchmark."
    write_text(TASK / "paper_architecture/paper_experiment_architecture.md", prose)
    review = """# Adversarial Paper Self-Review

## Contribution — pass with scope boundary

The contribution is the modular safety-assurance architecture and its retained positive, negative, and structural evidence chain. The paper must not present a global Full FAS-CBF superiority result.

## Writing clarity — pass if terminology remains fixed

Define Start-Safe, Feasibility-Aware, Risk-Aware V1, DT Verification, Predictive Recovery, and HCE separately. Define `h`, metric clearance, mesh collision, and GSplat overlap proxy before reporting numbers.

## Experimental strength — needs claim restraint, not a new experiment in this task

Module-level active/formal evidence exists, but a common fully activated learned-map paired superiority cohort does not. State configuration, cohort, and result type in every caption and table.

## Evaluation completeness — pass for modular framing

E1–E6 expose saturation, one-step correction failure, recovery exhaustion, ETH3D H3 activation absence, and the scope of external case studies rather than suppressing them.

## Method design soundness — pass with explicit limitations

Do not portray the architecture as deployment-certified or empirically planner-agnostic across all maps. A future global-superiority claim requires separately authorized, outcome-blind, fully activated paired evidence.
"""
    write_text(TASK / "paper_architecture/reviewer_adversarial_self_review.md", review)
    print("PASS_PAPER_EXPERIMENT_ARCHITECTURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
