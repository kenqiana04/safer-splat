"""Validate the compact blocked-state evidence without materializing data."""
from __future__ import annotations

from arkitscenes_handoff_common import validate_access_gate_outputs


def main() -> None:
    result = validate_access_gate_outputs()
    assert result["validation_pass"], result
    print("FRAME_JOIN_GATE_VALIDATION_PASS")


if __name__ == "__main__":
    main()
