#!/usr/bin/env python3
"""Static official-source audit for zero-valid-depth frame semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_common import sha256_file, write_json


def numbered_excerpt(lines: list[str], start: int, end: int) -> str:
    return "\n".join(f"{index}: {lines[index - 1]}" for index in range(start, end + 1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--microtest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    splatam_path = args.source.resolve() / "scripts" / "splatam.py"
    lines = splatam_path.read_text(encoding="utf-8").splitlines()
    microtest = json.loads(args.microtest.read_text(encoding="utf-8"))
    source_text = "\n".join(lines)
    facts = {
        "source_head": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
        "source_file": str(splatam_path),
        "source_sha256": sha256_file(splatam_path),
        "first_frame_depth_mask_line": 196,
        "first_frame_uses_depth_gt_zero": "mask = (depth > 0)" in source_text,
        "first_frame_explicit_zero_count_skip": False,
        "first_frame_scene_radius_uses_max_depth": "torch.max(depth)/scene_radius_depth_ratio" in source_text,
        "loss_mask_uses_depth_gt_zero": "mask = (curr_data['depth'] > 0)" in source_text,
        "tracking_depth_uses_sum": "[mask].sum()" in source_text,
        "mapping_depth_uses_mean": "[mask].mean()" in source_text,
        "rgb_mapping_loss_independent_of_depth_mask": "0.8 * l1_loss_v1" in source_text,
        "densification_intersects_valid_depth": "non_presence_mask = non_presence_mask & valid_depth_mask.reshape(-1)" in source_text,
        "official_zero_depth_frame_skip_logic": False,
        "first_frame_and_later_frame_behavior_different": True,
    }
    compatibility = {
        "status": "FAIL_OFFICIAL_SPLATAM_ZERO_VALID_DEPTH_COMPATIBILITY",
        "zero_valid_depth_safe_without_algorithm_change": False,
        "first_frame": {
            "safe": False,
            "reason": "empty initialization point cloud is not explicitly skipped and scene_radius becomes zero",
        },
        "later_tracking": {
            "depth_reduction_finite": True,
            "reason": "empty masked sum evaluates to zero, while RGB behavior depends on tracking flags",
        },
        "later_mapping": {
            "depth_reduction_finite": False,
            "reason": "official non-tracking depth loss calls mean() on the empty masked tensor",
        },
        "densification": {
            "safe": False,
            "reason": "non-presence is tested before intersection with valid-depth; no explicit empty-frame skip contract exists",
        },
        "microtest_status": microtest["status"],
        "semantics_unresolved": False,
        "mapper_instantiated": False,
        "optimizer_created": False,
    }
    report = f"""# Official SplaTAM zero-valid-depth source audit

Authority: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
File SHA-256: `{facts['source_sha256']}`

## First-frame initialization

```python
{numbered_excerpt(lines, 190, 202)}
```

There is no official zero-count skip before the initial point cloud and parameter construction. The same function later derives `scene_radius` from the maximum depth, which is zero for an all-zero frame.

## Tracking and mapping loss

```python
{numbered_excerpt(lines, 260, 291)}
```

Tracking uses an empty masked `sum`, which is finite zero. Mapping uses an empty masked `mean`, which is nonfinite. The RGB mapping loss is structurally independent, but it does not make the combined weighted loss finite when depth is NaN.

## New-frame densification

```python
{numbered_excerpt(lines, 384, 412)}
```

The official code intersects the non-presence mask with positive depth, but only after deciding that the pre-intersection non-presence mask is nonempty. No explicit zero-depth-frame skip establishes a safe finite mapper contract.

## Decision

`{compatibility['status']}`. This is a source and forward-reduction audit only: no mapper, optimizer, backward, parameter update, or real scene execution occurred.
"""
    report = "\n".join(line.rstrip() for line in report.splitlines()) + "\n"
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "splatam_zero_mask_source_audit.md").write_text(report, encoding="utf-8")
    write_json(args.output_root / "splatam_mask_compatibility_decision.json", compatibility)
    write_json(args.output_root / "splatam_zero_mask_source_facts.json", facts)
    print(compatibility["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
