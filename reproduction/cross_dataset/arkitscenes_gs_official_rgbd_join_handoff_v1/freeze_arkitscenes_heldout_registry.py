"""Keep held-out selection absent until a primary is frozen."""
from __future__ import annotations

from arkitscenes_handoff_common import FINAL_STATUS, ensure_preflight_outputs


def main() -> None:
    ensure_preflight_outputs()
    print(f"NOT_AUTHORIZED_DUE_TO_{FINAL_STATUS}")


if __name__ == "__main__":
    main()
