#!/usr/bin/env python3
"""Static integrity gate for the frozen V1R6 launch payload."""
from __future__ import annotations

import hashlib
import json
import shlex
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
IDENTITY = json.loads((ROOT / "V1R6_RUN_IDENTITY.json").read_text(encoding="utf-8"))
COMMAND = ROOT / "v1r6_exact_training_command.sh"


def main() -> int:
    data = COMMAND.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), "command_bom"
    assert b"\r\n" not in data, "command_crlf"
    assert data.endswith(b"\n"), "command_final_lf"
    assert IDENTITY["run_label"] == "V1R6"
    assert IDENTITY["seed"] == 20260716
    assert IDENTITY["timestamp"] == "20260717_070309"
    assert IDENTITY["max_formal_attempts"] == 1
    assert not IDENTITY["resume_allowed"] and not IDENTITY["retry_allowed"]
    line = next(line for line in data.decode("utf-8").splitlines() if line.startswith("ns-train "))
    tokens = shlex.split(line)
    assert len(tokens) == 71, len(tokens)
    assert tokens[tokens.index("--machine.seed") + 1] == "20260716"
    assert tokens[tokens.index("--max-num-iterations") + 1] == "30000"
    assert "--experiment-name" in tokens and "tum_fr1_room_splatfacto_v1r6" in tokens
    assert "--timestamp" in tokens and "20260717_070309" in tokens
    assert "gsplat_1_4_0_pt21cu118" in data.decode("utf-8")
    print(json.dumps({
        "validator": "PASS_READY_FOR_FORMAL_TRAINING_EXECUTION_V1R6_AUTHORIZATION",
        "command_sha256": hashlib.sha256(data).hexdigest(),
        "command_tokens": len(tokens),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
