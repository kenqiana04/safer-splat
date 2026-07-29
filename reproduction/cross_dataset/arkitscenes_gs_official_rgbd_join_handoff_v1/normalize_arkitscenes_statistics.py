"""Do not rank candidates before access to the authoritative component exists."""
from __future__ import annotations

from arkitscenes_handoff_common import ensure_gate_outputs


def main() -> None:
    ensure_gate_outputs()
    print("NOT_AUTHORIZED_DUE_TO_COMPONENT_ACCESS_GATE")


if __name__ == "__main__":
    main()
