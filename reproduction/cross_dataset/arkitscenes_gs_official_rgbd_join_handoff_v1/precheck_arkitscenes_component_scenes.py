"""Prevent map structure inspection before gated-content approval."""
from __future__ import annotations

from arkitscenes_handoff_common import compact_path, ensure_preflight_outputs, read_json


def main() -> None:
    ensure_preflight_outputs()
    print(read_json(compact_path("arkitscenes_component_scene_precheck.json"))["status"])


if __name__ == "__main__":
    main()
