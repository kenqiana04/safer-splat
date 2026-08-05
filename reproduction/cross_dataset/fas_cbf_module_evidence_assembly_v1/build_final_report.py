#!/usr/bin/env python3
"""Write the compact final assembly report and Draft PR body from audited matrices."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_text


def main() -> int:
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    claims = load_json("claim_audit/claim_evidence_matrix.json")["claims"]
    decision = load_json("minimal_remaining_experiment/minimal_remaining_experiment.json")
    positive = [row["evidence_id"] for row in sources if row["polarity"] == "positive"]
    negative = [row["evidence_id"] for row in sources if row["polarity"] == "negative"]
    structural = [row["evidence_id"] for row in sources if row["polarity"] == "structural"]
    report = f"""# ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1

## Outcome

`{decision['FINAL_STATUS']}`

This package integrates {len(sources)} frozen compact evidence sources. It runs no new map training, scenario search, controller rollout, tuning, or dataset switch. It preserves PR #81 Case D: ETH3D provides learned-map viability and a structural activation limit, not a DT-invalidity result.

## Evidence roles

- **Official SAFER-map cases:** configuration-specific active module evidence for Start-Safe, Risk-Aware efficiency, DT risk detection, and Predictive Recovery.
- **Replica GT-derived Gaussian map:** clean shared-route controller benchmark; all 99 map-admissible routes succeeded for all methods with zero official-mesh collisions, so outcome saturation prevents superiority inference.
- **ETH3D learned 3DGS:** one external learned map passed minimum controller viability, but its frozen state set contains zero strict endpoint-unsafe/QP-feasible H3 cases after 200000 shadow tuples; no V2 registry, smoke, or formal rollout was permitted.
- **TUM learned-SLAM case study:** shadow precursor and bounded strict-trigger intervention evidence using a GSplat-overlap proxy, not official mesh collision.

## Claim audit

- Configuration-specific claims: {', '.join(row['claim_id'] for row in claims if row['status'] == 'CONFIGURATION_SPECIFIC')}.
- Partially supported architecture framing: {', '.join(row['claim_id'] for row in claims if row['status'] == 'PARTIALLY_SUPPORTED')}.
- Prohibited stronger claims: {', '.join(row['claim_id'] for row in claims if row['status'] == 'PROHIBITED')}.

Full FAS-CBF superiority over SAFER is **not established**. The paper should be framed as a modular safety-assurance architecture supported by complementary, configuration-bounded evidence rather than a global superiority benchmark.

## Positive, negative, and structural evidence

- Positive: {', '.join(positive)}.
- Negative ablations: {', '.join(negative)}.
- Structural boundaries: {', '.join(structural)}.

## Paper architecture

E1 separates map roles; E2 reports Start-Safe with original/post-repair separation; E3 reports constraint/efficiency only within compatible configurations; E4 presents DT detection, precursor, and one-step negative evidence; E5 presents predictive recovery, HCE, and exhaustion; E6 reports Replica saturation and ETH3D learned-map activation limits without a superiority claim.

## Decision

- FINAL_STATUS: `{decision['FINAL_STATUS']}`
- FINAL_DECISION: `{decision['FINAL_DECISION']}`
- Only next task: `{decision['ONLY_NEXT_TASK']}`
"""
    write_text(TASK / "report/REPORT_ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1.md", report)
    pr = f"""## Scope

PR #81 is preserved at its frozen head. This PR assembles existing compact GT-derived and learned-map evidence only; it performs no new experiment, training, scenario search, controller rollout, tuning, or dataset switch.

## Evidence and claim boundary

- {len(sources)} source reports are frozen by commit, Git blob, and SHA-256 in the provenance ledger.
- Map roles remain separated: official SAFER-map module studies, Replica GT-derived Gaussian benchmark, ETH3D learned 3DGS external carrier, and TUM learned-SLAM case study.
- The module matrix preserves active, shadow, diagnostic, negative-ablation, and structural evidence separately.
- DT taxonomy separates endpoint, segment, margin, H-step predicted, executed collision/overlap, and bounded intervention evidence.
- Replica saturation and ETH3D Case D rule out a Full FAS-CBF-versus-SAFER global-superiority claim.

## Paper framing and decision

Frame the work as a modular safety-assurance architecture with configuration-specific module claims. ETH3D shows learned-map viability and an explicit activation limit, not deployment safety.

- FINAL_STATUS: `{decision['FINAL_STATUS']}`
- FINAL_DECISION: `{decision['FINAL_DECISION']}`
- Only next task: `{decision['ONLY_NEXT_TASK']}`
"""
    write_text(TASK / "report/DRAFT_PR_BODY.md", pr)
    print("PASS_FINAL_REPORT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
