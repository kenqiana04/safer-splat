"""Do not rank candidates before access to the authoritative component exists."""
from __future__ import annotations

from arkitscenes_handoff_common import compact_path, ensure_preflight_outputs, read_json


def main() -> None:
    ensure_preflight_outputs()
    print(read_json(compact_path("arkitscenes_metadata_summary.json"))["status"])


if __name__ == "__main__":
    main()
