"""Deliberately execute no payload download while component access is blocked."""
from __future__ import annotations

from arkitscenes_handoff_common import ensure_gate_outputs


def main() -> None:
    ensure_gate_outputs()
    print("NO_PAYLOAD_DOWNLOAD_AUTHORIZED")


if __name__ == "__main__":
    main()
