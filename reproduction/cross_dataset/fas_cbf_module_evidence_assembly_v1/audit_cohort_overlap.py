#!/usr/bin/env python3
"""Record known cohort relationships and prohibit duplicate statistical pooling."""
from __future__ import annotations

from evidence_common import TASK, write_json


def main() -> int:
    audit = {
        "status": "PASS_COHORT_OVERLAP_AUDIT",
        "pooling_permitted": False,
        "rules": ["Do not pool controller steps as trials.", "Do not pool original and post-repair flights.", "Do not pool dense-flight H1/H2/H3 nested counts.", "Do not pool HCE activated cohort with full100 recovery outcomes.", "Do not pool Replica GT-derived and ETH3D learned-map outcomes."],
        "known_overlap_or_nesting": [
            {"sources": ["E04_STARTGUARD_TRIAL57", "E05_STARTGUARD_FLIGHT100"], "relation": "trial57 is retained within flight100 original history", "treatment": "report separately"},
            {"sources": ["E11_DT_DETECTION", "E13_V4C_H3", "E14_V4C_TUNED_H2", "E15_HCE_HELDOUT", "E16_TRIAL20_BOUNDARY"], "relation": "dense-flight families with different horizons and selected subcohorts", "treatment": "configuration-specific, no pooled effect size"},
            {"sources": ["E17_TUM_DT_FORENSICS", "E18_TUM_V4C_INTERVENTION"], "relation": "shared TUM boundary context but distinct shadow and intervention protocols", "treatment": "mechanism sequence only"}
        ]
    }
    write_json(TASK / "config_compatibility/cohort_overlap_audit.json", audit)
    print("PASS_COHORT_OVERLAP_AUDIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
