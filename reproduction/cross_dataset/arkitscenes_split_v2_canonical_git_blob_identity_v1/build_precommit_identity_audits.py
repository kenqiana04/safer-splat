"""Record producer and attribute scope evidence before the normal commit."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from canonical_identity_common import V2_ROOT, sha256_file, write_json


def canonical_lf_text_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        raise SystemExit("BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION")
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True); args = parser.parse_args()
    v2 = args.repo / V2_ROOT; writer = v2 / "arkitscenes_split_v2_common.py"; attributes = v2 / ".gitattributes"; root_attributes = args.repo / ".gitattributes"
    writer_text = writer.read_text(encoding="utf-8"); attribute_lines = attributes.read_text(encoding="utf-8").splitlines()
    required = {"*.csv text eol=lf", "*.json text eol=lf", "*.md text eol=lf", "*.py text eol=lf"}
    csv_audit = {"status": "PASS_CANONICAL_CSV_WRITER" if 'lineterminator="\\n"' in writer_text and 'newline=""' in writer_text else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "producer_path": str(writer.relative_to(args.repo)).replace("\\", "/"), "producer_canonical_lf_sha256": canonical_lf_text_sha256(writer), "explicit_lineterminator_lf": 'lineterminator="\\n"' in writer_text, "utf8_newline_empty": 'newline=""' in writer_text, "algorithm_change": False}
    attr_audit = {"status": "PASS_GITATTRIBUTES_SCOPE" if required <= set(attribute_lines) else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "path": str(attributes.relative_to(args.repo)).replace("\\", "/"), "canonical_lf_sha256": canonical_lf_text_sha256(attributes), "required_rules": sorted(required), "actual_rules": attribute_lines, "binary_patterns_added": False, "higher_level_gitattributes_exists": root_attributes.is_file(), "higher_level_gitattributes_sha256": sha256_file(root_attributes) if root_attributes.is_file() else None}
    write_json(args.output_root / "csv_writer_canonicalization_audit.json", csv_audit); write_json(args.output_root / "gitattributes_scope_audit.json", attr_audit)
    print(csv_audit["status"], attr_audit["status"])
    return 0 if csv_audit["status"].startswith("PASS") and attr_audit["status"].startswith("PASS") else 2


if __name__ == "__main__": raise SystemExit(main())
