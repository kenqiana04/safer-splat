"""Prevent frame joining before component access is proven."""
from __future__ import annotations

from arkitscenes_handoff_common import FINAL_STATUS, ensure_preflight_outputs


def main() -> None:
    ensure_preflight_outputs()
    print(FINAL_STATUS)


if __name__ == "__main__":
    main()
