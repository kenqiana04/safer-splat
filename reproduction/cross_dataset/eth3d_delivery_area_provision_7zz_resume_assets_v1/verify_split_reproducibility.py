#!/usr/bin/env python3
"""Verify the frozen split byte-for-byte in three fresh Python processes."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from task_config import TASK_ROOT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    script = TASK_ROOT / "audit_rig_dslr_and_freeze_split.py"
    split = TASK_ROOT / "split" / "pose_block_split_v1.json"
    records = []
    for index in range(1, 4):
        result = subprocess.run([sys.executable, str(script)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (TASK_ROOT / "logs" / f"split_fresh_process_{index}.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"SPLIT_FRESH_PROCESS_FAILURE {index} {result.stdout[-2000:]}")
        records.append({"process_index": index, "file_sha256": sha256(split),
                        "semantic_sha256": json.loads(split.read_text(encoding="utf-8"))["split_sha256"]})
    if len({row["file_sha256"] for row in records}) != 1 or len({row["semantic_sha256"] for row in records}) != 1:
        raise RuntimeError(f"SPLIT_REPRODUCIBILITY_FAILURE {records}")
    output = {"status": "PASS_THREE_FRESH_PROCESS_BYTE_REPRODUCIBILITY", "process_count": 3, "records": records}
    (TASK_ROOT / "split" / "split_reproducibility.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (TASK_ROOT / "split" / "fresh_process_split_reproducibility.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output["status"], records[0]["semantic_sha256"])


if __name__ == "__main__":
    main()
