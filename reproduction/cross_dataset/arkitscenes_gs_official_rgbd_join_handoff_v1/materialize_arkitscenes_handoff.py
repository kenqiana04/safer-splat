"""Deliberately leave materialization absent behind the access gate."""
from __future__ import annotations

from arkitscenes_handoff_common import ensure_gate_outputs


def main() -> None:
    ensure_gate_outputs()
    print("NO_MATERIALIZATION_AUTHORIZED")


if __name__ == "__main__":
    main()
