"""Do not infer scene/video identities behind a failed access gate."""
from __future__ import annotations

from arkitscenes_handoff_common import compact_path, ensure_preflight_outputs, read_json


def main() -> None:
    ensure_preflight_outputs()
    print(read_json(compact_path("arkitscenes_scene_id_join_audit.json"))["status"])


if __name__ == "__main__":
    main()
