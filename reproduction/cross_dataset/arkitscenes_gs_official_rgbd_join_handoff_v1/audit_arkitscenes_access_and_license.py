"""Perform the zero-payload component-access gate."""
from __future__ import annotations

from arkitscenes_handoff_common import FINAL_STATUS, run_authorized_preflight


def main() -> None:
    result = run_authorized_preflight()
    assert result["status"] == FINAL_STATUS
    print(FINAL_STATUS)


if __name__ == "__main__":
    main()
