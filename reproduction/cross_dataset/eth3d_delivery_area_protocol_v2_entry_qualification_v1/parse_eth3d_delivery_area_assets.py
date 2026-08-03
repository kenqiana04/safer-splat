#!/usr/bin/env python3
"""Parse Delivery Area asset metadata and issue HEAD-only archive checks."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import urllib.request
from pathlib import Path


ASSETS = [
    ("delivery_area_dslr_undistorted.7z", "HIGH_RES_DSLR", "0.5 GB", "CROSS_VIEW_EVALUATION_ONLY", "CROSS_VIEW_EVALUATION", "required"),
    ("delivery_area_dslr_jpg.7z", "HIGH_RES_DSLR", "0.4 GB", "NOT_REQUIRED", "NONE", "rejected"),
    ("delivery_area_dslr_raw.7z", "HIGH_RES_DSLR", "1.1 GB", "NOT_REQUIRED", "NONE", "rejected"),
    ("delivery_area_scan_raw.7z", "SHARED_REFERENCE", "0.4 GB", "OPTIONAL_DIAGNOSTIC_ONLY", "FUTURE_DIAGNOSTIC", "rejected"),
    ("delivery_area_scan_clean.7z", "SHARED_REFERENCE", "0.4 GB", "REFERENCE_ORACLE_ONLY", "REFERENCE_ORACLE", "required"),
    ("delivery_area_dslr_scan_eval.7z", "HIGH_RES_DSLR", "0.1 GB", "CROSS_VIEW_EVALUATION_ONLY", "CROSS_VIEW_EVALUATION", "required"),
    ("delivery_area_dslr_occlusion.7z", "HIGH_RES_DSLR", "0.1 GB", "CROSS_VIEW_EVALUATION_ONLY", "CROSS_VIEW_EVALUATION", "required"),
    ("delivery_area_dslr_depth.7z", "HIGH_RES_DSLR", "0.4 GB", "CROSS_VIEW_EVALUATION_ONLY", "CROSS_VIEW_EVALUATION", "required"),
    ("delivery_area_rig_undistorted.7z", "LOW_RES_RIG", "0.3 GB", "MAPPING_INPUT_ONLY", "TRAIN_INPUT_ROOT", "required"),
    ("delivery_area_rig.7z", "LOW_RES_RIG", "0.3 GB", "NOT_REQUIRED", "NONE", "rejected"),
    ("delivery_area_rig_scan_eval.7z", "LOW_RES_RIG", "0.1 GB", "HELDOUT_EVALUATION_ONLY", "EVAL_ORACLE_ROOT", "required"),
    ("delivery_area_rig_occlusion.7z", "LOW_RES_RIG", "0.1 GB", "HELDOUT_EVALUATION_ONLY", "EVAL_ORACLE_ROOT", "required"),
    ("delivery_area_rig_depth.7z", "LOW_RES_RIG", "0.6 GB", "HELDOUT_EVALUATION_ONLY", "EVAL_ORACLE_ROOT", "required"),
    ("delivery_area_rig_stereo_pairs_gt.7z", "LOW_RES_RIG", "0.9 GB", "PROHIBITED_AS_MAPPING_INPUT", "NONE", "rejected"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RedirectRecorder(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"status": code, "from": req.full_url, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def head(url: str) -> dict:
    recorder = RedirectRecorder()
    opener = urllib.request.build_opener(recorder)
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "safer-splat-protocol-v2-head-audit/1.0", "Accept": "*/*"},
    )
    with opener.open(req, timeout=90) as response:
        return {
            "requested_url": url,
            "redirect_chain": recorder.chain,
            "final_url": response.geturl(),
            "http_status": response.status,
            "retrieval_utc": utc_now(),
            "content_length": response.headers.get("Content-Length"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "content_type": response.headers.get("Content-Type"),
            "accept_ranges": response.headers.get("Accept-Ranges"),
            "content_disposition": response.headers.get("Content-Disposition"),
            "response_body_bytes": 0,
            "method": "HEAD",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    auth = root / "official_authority"
    out = root / "asset_manifest"
    out.mkdir(parents=True, exist_ok=True)
    page = (auth / "eth3d_mvs_datasets.html").read_text(encoding="utf-8", errors="replace")

    records = []
    head_records = []
    for filename, variant, declared_size, role, physical_root, disposition in ASSETS:
        pattern = re.compile(re.escape(filename) + r".*?\(\s*" + re.escape(declared_size) + r"\s*\)", re.I | re.S)
        page_match = bool(pattern.search(page))
        url = f"https://www.eth3d.net/data/{filename}"
        head_meta = head(url)
        head_meta["filename"] = filename
        head_records.append(head_meta)
        value, unit = declared_size.split()
        declared_bytes = int(float(value) * (1_000_000_000 if unit == "GB" else 1_000_000))
        records.append(
            {
                "official_filename": filename,
                "dataset_variant": variant,
                "official_declared_size": declared_size,
                "official_declared_size_bytes_decimal": declared_bytes,
                "official_page_match": page_match,
                "official_download_url": url,
                "final_official_download_url": head_meta["final_url"],
                "redirect_chain": head_meta["redirect_chain"],
                "http_status": head_meta["http_status"],
                "content_length": int(head_meta["content_length"]) if head_meta["content_length"] else None,
                "etag": head_meta["etag"],
                "last_modified": head_meta["last_modified"],
                "mime": head_meta["content_type"],
                "archive_format": "7z",
                "expected_internal_semantics": "posed undistorted RGB and COLMAP text calibration" if "undistorted" in filename else "laser-scan-derived evaluation/reference data" if any(x in filename for x in ["depth", "scan", "occlusion", "stereo_pairs_gt"]) else "distorted source imagery",
                "project_role": role,
                "physical_root": physical_root,
                "allowed_phase": "FUTURE_BOUNDED_ASSET_AUDIT_ONLY" if disposition == "required" else "NOT_AUTHORIZED_IN_NEXT_TASK",
                "prohibited_phase": "MAPPING_TRAINING" if role != "MAPPING_INPUT_ONLY" else "CURRENT_METADATA_ONLY_TASK",
                "future_sha_verification_method": "stream archive once in an explicitly authorized acquisition task while computing SHA-256; compare immutable byte count and archive listing",
                "disposition": disposition,
                "mapping_input_prohibited": role != "MAPPING_INPUT_ONLY",
                "head_only": True,
                "response_body_bytes": 0,
            }
        )

    failures = [r["official_filename"] for r in records if not r["official_page_match"] or r["http_status"] not in (200, 204)]
    (out / "official_asset_manifest.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    (out / "http_head_validation.json").write_text(
        json.dumps(
            {
                "status": "PASS" if not failures else "FAIL",
                "method": "HEAD_ONLY",
                "head_count": len(head_records),
                "get_body_count": 0,
                "response_body_bytes": 0,
                "failures": failures,
                "records": head_records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    fields = list(records[0].keys())
    with (out / "official_asset_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({k: json.dumps(v, separators=(",", ":")) if isinstance(v, (list, dict)) else v for k, v in record.items()})
    role_matrix = {
        "role_enum": [
            "MAPPING_INPUT_ONLY",
            "HELDOUT_EVALUATION_ONLY",
            "REFERENCE_ORACLE_ONLY",
            "CROSS_VIEW_EVALUATION_ONLY",
            "OPTIONAL_DIAGNOSTIC_ONLY",
            "PROHIBITED_AS_MAPPING_INPUT",
            "NOT_REQUIRED",
        ],
        "assets": [{"filename": r["official_filename"], "role": r["project_role"], "physical_root": r["physical_root"]} for r in records],
    }
    (out / "asset_role_matrix.json").write_text(json.dumps(role_matrix, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "asset_count": len(records), "head_count": len(head_records), "failures": failures}, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
