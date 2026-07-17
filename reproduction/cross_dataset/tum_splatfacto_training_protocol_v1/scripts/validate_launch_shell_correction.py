#!/usr/bin/env python3
"""Validate the launch-shell correction and record a pass or explicit block."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
PASS = "PASS_READY_FOR_FORMAL_TRAINING_EXECUTION_AFTER_LAUNCH_SHELL_CORRECTION"


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def git(*args: str) -> int:
    return subprocess.run(["git", *args], cwd=REPO, check=False).returncode


def main() -> int:
    before = load("activation_probe_before.json")
    after = load("activation_probe_after.json")
    semantic = load("command_semantic_comparison.json")
    result = load("launch_shell_correction_result.json")
    server = load("activation_probe_server_verification.json")
    config_unchanged = git("diff", "--exit-code", "6843fa477adc7f07acdfdb270ad7e4e3349da904", "--", str(ROOT / "frozen_training_config.json")) == 0
    server_ok = server["status"] == "PASS_SERVER_CHECKOUT_AND_ACTIVATION_ONLY_PROBE"
    passed = all((
        before["status"] == "REPRODUCED_PRE_ACTIVATION_NOUNSET_FAILURE",
        after["status"] == "PASS_CONDA_ACTIVATION_THEN_NOUNSET",
        semantic["ns_train_tokens_equal"],
        semantic["training_argument_difference_count"] == 0,
        config_unchanged,
        server_ok,
    ))
    status = PASS if passed else result["status"]
    payload = {
        "status": status,
        "checks": {
            "old_failure_reproduced": before["status"] == "REPRODUCED_PRE_ACTIVATION_NOUNSET_FAILURE",
            "activation_after_passed": after["status"] == "PASS_CONDA_ACTIVATION_THEN_NOUNSET",
            "tokens_unchanged": semantic["ns_train_tokens_equal"],
            "config_unchanged": config_unchanged,
            "server_checkout_verified": server_ok,
        },
        "training_iterations_executed": 0,
        "checkpoint_created": False,
        "G1_allowed": False,
        "unresolved_critical_fields": [] if passed else ["git_transport_fetch" if result["status"] == "BLOCKED_BY_GIT_TRANSPORT_TIMEOUT" else "server_checkout_verification"],
        "unresolved_noncritical_fields": [],
    }
    (ROOT / "validation_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(status)


if __name__ == "__main__":
    main()
