"""Expose the frozen README-to-component authority decision."""
from __future__ import annotations

from arkitscenes_handoff_common import compact_path, ensure_preflight_outputs, read_json


def main() -> None:
    ensure_preflight_outputs()
    result = read_json(compact_path("arkitscenes_component_authority.json"))
    print(result["status"])


if __name__ == "__main__":
    main()
