"""Update only V2 records derived from the two manifest raw-byte identities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical_identity_common import CONTRACT_RELATIVE, PR68, V2_ROOT, git_file, write_json


def dump_compact(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True); args = parser.parse_args()
    v2 = args.repo / V2_ROOT
    contract = json.loads((args.repo / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    old = json.loads(git_file(args.repo, PR68, CONTRACT_RELATIVE).decode("utf-8"))
    change = {"old_split_identity_sha256": old["split_identity_sha256"], "new_split_identity_sha256": contract["split_identity_sha256"], "old_train_manifest_sha256": old["train_manifest_sha256"], "new_train_manifest_sha256": contract["train_manifest_sha256"], "old_heldout_manifest_sha256": old["heldout_manifest_sha256"], "new_heldout_manifest_sha256": contract["heldout_manifest_sha256"], "change_reason": "EOL_CANONICALIZATION_ONLY", "semantic_change_count": 0}
    for relative, key in ((Path("run_manifest.json"), "split_identity_sha256"), (Path("downstream_handoff.json"), "v2_split_identity_sha256")):
        path = v2 / relative; value = json.loads(path.read_text(encoding="utf-8")); value[key] = contract["split_identity_sha256"]; value["identity_policy"] = "CANONICAL_GIT_BLOB_BYTES_SHA256_V1"; value["manifest_identity_change"] = change; dump_compact(path, value)
    fresh_path = v2 / "validation/fresh_process_reproducibility.json"
    fresh = json.loads(fresh_path.read_text(encoding="utf-8"))
    for run in fresh["runs"]:
        run["train_manifest_sha256"] = contract["train_manifest_sha256"]
        run["heldout_manifest_sha256"] = contract["heldout_manifest_sha256"]
        run["split_identity_sha256"] = contract["split_identity_sha256"]
    fresh["identity_policy"] = "CANONICAL_GIT_BLOB_BYTES_SHA256_V1"
    fresh["manifest_identity_change"] = change
    fresh["raw_identity_update_note"] = "Only pre-commit CRLF generation identities were replaced with canonical LF Git-blob identities; the three frozen semantic regeneration results are unchanged."
    dump_compact(fresh_path, fresh)
    report_path = v2 / "REPORT_REVISE_ARKITSCENES_SPATIAL_GROUP_SPLIT_CONTRACT_V2.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "## Canonical Git-blob identity correction\n"
    if marker in report: report = report.split(marker, 1)[0].rstrip() + "\n\n"
    report += marker + "\nThe split records, groups, frame order, thresholds, and DP result are unchanged. The two CSV identities were corrected from pre-commit CRLF generation hashes to committed LF Git-blob SHA-256 values under `CANONICAL_GIT_BLOB_BYTES_SHA256_V1`. Legacy values remain in the V2 contract as non-authoritative historical evidence.\n\n"
    report += f"- TRAIN legacy `{old['train_manifest_sha256']}` → canonical `{contract['train_manifest_sha256']}`\n- HELDOUT legacy `{old['heldout_manifest_sha256']}` → canonical `{contract['heldout_manifest_sha256']}`\n- Split identity `{old['split_identity_sha256']}` → `{contract['split_identity_sha256']}`; reason: EOL canonicalization only, semantic change count 0.\n"
    report_path.write_text(report, encoding="utf-8", newline="\n")
    crosswalk = {"status": "PASS_LEGACY_TO_CANONICAL_CROSSWALK", "identity_policy": "CANONICAL_GIT_BLOB_BYTES_SHA256_V1", "records": change, "legacy_values_retained_in": str(CONTRACT_RELATIVE), "semantic_change_count": 0}
    write_json(args.output_root / "legacy_to_canonical_identity_crosswalk.json", crosswalk)
    print("PASS_UPDATED_V2_RAW_IDENTITY_DERIVATIVES")
    return 0


if __name__ == "__main__": raise SystemExit(main())
