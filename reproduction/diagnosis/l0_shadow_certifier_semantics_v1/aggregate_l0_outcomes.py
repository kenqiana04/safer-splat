from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping


TYPED_L0_STATUSES = ("PASS", "FAIL", "UNKNOWN")
NOT_OBSERVABLE = "L0_OUTCOME_DISTRIBUTION_NOT_OBSERVABLE_FROM_FROZEN_RESULTS"


def classify_l0_status(value: object) -> str:
    return value if isinstance(value, str) and value in TYPED_L0_STATUSES else "OTHER"


def mapping_mismatch(*, raw_status: object, adapter_status: object, raw_pass_tokens: set[str]) -> bool:
    raw_is_pass = isinstance(raw_status, str) and raw_status in raw_pass_tokens
    adapter_is_pass = adapter_status == "PASS"
    return raw_is_pass != adapter_is_pass


def aggregate_records(records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    backend_counts: Counter[str] = Counter()
    total = 0
    status_field_count = 0
    reason_field_count = 0
    backend_field_count = 0
    for record in records:
        total += 1
        if "l0_status" in record:
            status_field_count += 1
            status_counts[classify_l0_status(record.get("l0_status"))] += 1
        if "l0_reason" in record:
            reason_field_count += 1
            reason_counts[str(record.get("l0_reason"))] += 1
        if "l0_backend" in record:
            backend_field_count += 1
            backend_counts[str(record.get("l0_backend"))] += 1
    if total and status_field_count == 0:
        return {
            "observable": False,
            "outcome": NOT_OBSERVABLE,
            "row_count": total,
            "counts": None,
            "reason_counts": None,
            "backend_counts": None,
        }
    if status_field_count != total:
        raise ValueError(f"PARTIAL_L0_STATUS_OBSERVABILITY:{status_field_count}/{total}")
    return {
        "observable": True,
        "outcome": "L0_OUTCOME_DISTRIBUTION_OBSERVABLE_FROM_FROZEN_RESULTS",
        "row_count": total,
        "counts": {name: status_counts.get(name, 0) for name in (*TYPED_L0_STATUSES, "OTHER")},
        "reason_counts": dict(sorted(reason_counts.items())) if reason_field_count else None,
        "backend_counts": dict(sorted(backend_counts.items())) if backend_field_count else None,
        "l0_reason_field_count": reason_field_count,
        "l0_backend_field_count": backend_field_count,
    }


def iter_jsonl(paths: list[Path]):
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"INVALID_JSONL:{path}:{line_number}") from exc


def write_csv(path: Path, header: tuple[str, str], values: Mapping[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for key, count in values.items():
            writer.writerow((key, count))


def write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-pass frozen L0 result aggregation")
    parser.add_argument("--formal-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=14122)
    parser.add_argument("--expected-files", type=int, default=100)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scan_lock = args.output_dir / "L0_STREAMING_SCAN_LOCK.json"
    if scan_lock.exists():
        raise SystemExit("REFUSING_SECOND_L0_STREAMING_SCAN")
    paths = sorted(args.formal_root.glob("trial-*/attempt-*/run/instrumentation/shadow_certificate_result_log.jsonl"))
    if len(paths) != args.expected_files:
        raise SystemExit(f"FORMAL_RESULT_FILE_COUNT_MISMATCH:{len(paths)}")

    write_json(scan_lock, {"scan_started": True, "streaming_scan_count": 1, "raw_rows_printed": 0})
    summary = aggregate_records(iter_jsonl(paths))
    if summary["row_count"] != args.expected_rows:
        raise SystemExit(f"FORMAL_RESULT_ROW_COUNT_MISMATCH:{summary['row_count']}")
    if not summary["observable"]:
        write_json(args.output_dir / "l0_outcome_summary.json", summary)
        print(json.dumps({"outcome": summary["outcome"], "row_count": summary["row_count"]}, sort_keys=True))
        return 0

    counts = summary["counts"]
    assert isinstance(counts, dict)
    if sum(counts.values()) != args.expected_rows:
        raise SystemExit("L0_STATUS_ACCOUNTING_MISMATCH")
    write_csv(args.output_dir / "l0_status_distribution.csv", ("l0_status", "count"), counts)
    if summary["reason_counts"] is not None:
        write_csv(args.output_dir / "l0_reason_distribution.csv", ("l0_reason", "count"), summary["reason_counts"])
    if summary["backend_counts"] is not None:
        write_csv(args.output_dir / "l0_backend_distribution.csv", ("l0_backend", "count"), summary["backend_counts"])
    write_json(args.output_dir / "l0_outcome_summary.json", summary)
    print(json.dumps({"outcome": summary["outcome"], "row_count": summary["row_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
