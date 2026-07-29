"""Do not create an archive when no primary handoff tree exists."""
from __future__ import annotations

from arkitscenes_handoff_common import ensure_gate_outputs


def main() -> None:
    ensure_gate_outputs()
    print("NO_PACKAGE_AUTHORIZED")


if __name__ == "__main__":
    main()
