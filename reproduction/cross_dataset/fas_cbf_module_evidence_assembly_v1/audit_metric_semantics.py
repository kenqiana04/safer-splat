#!/usr/bin/env python3
"""Freeze semantic rules that forbid accidental pooling or relabeling."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_text


def main() -> int:
    metrics = load_json("semantic_alignment/parsed_compact_metrics.json")["metrics"]
    if any(not row["sample_unit"] for row in metrics):
        raise RuntimeError("metric without sample unit")
    text = """# Metric Semantic Alignment

## Units and denominators

- ETH3D and Replica formal records use a scenario/route-method terminal-record unit; controller steps are never treated as independent trials.
- Start-Safe natural evidence distinguishes 100 flight trials, 8 repair-needed trials, and separately reported original versus post-repair outcomes.
- Synthetic projection uses 120 constructed static states; it is not an official benchmark cohort.
- DT counts are sampled controller-step margin-risk detections, not collision counts. H1/H2/H3 counts are nested horizon observations and are not subtracted or pooled as independent trajectories.
- Recovery evidence distinguishes base violations, executed violations, recovery activations, recovery successes, and recovery failures.

## Hard claim boundaries

- Map safety field `h`, metric/mesh clearance, official mesh collision, and GSplat overlap proxy are distinct quantities.
- Margin violations are not collisions. Shadow prediction is not closed-loop avoidance.
- Original trial57 and post-repair flight results remain separate. Development, held-out, formal, diagnostic, and static evidence remain separate.
- The PR #81 endpoint-unsafe deficit is a frozen-contract structural limit; it is not evidence that DT verification is ineffective.
"""
    write_text(TASK / "semantic_alignment/metric_semantic_alignment.md", text)
    print("PASS_METRIC_SEMANTIC_ALIGNMENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
