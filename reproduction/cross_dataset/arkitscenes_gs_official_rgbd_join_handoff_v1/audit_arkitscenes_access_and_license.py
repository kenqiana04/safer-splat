"""Perform the zero-payload component-access gate."""
from __future__ import annotations

from arkitscenes_handoff_common import FINAL_STATUS, run_access_gate


def main() -> None:
    access = run_access_gate()
    assert access["status"] == FINAL_STATUS
    print(FINAL_STATUS)


if __name__ == "__main__":
    main()
