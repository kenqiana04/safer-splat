import json
from pathlib import Path


def test_all_fifteen_synthetic_records_are_frozen_and_reference_free():
    root=Path(__file__).resolve().parents[1]/"synthetic_cases"
    files=sorted(root.glob("SYN-*.json"))
    assert len(files)==15
    records=[json.loads(p.read_text(encoding="utf-8")) for p in files]
    assert [r["case_id"] for r in records]==[f"SYN-{i:02d}" for i in range(1,16)]
    assert all(r["deterministic"] and not r["reference_online_input"] for r in records)
    assert all(r["analytic_expected_status"] and r["exact_reason_code"] for r in records)
