"""Create or resume only the matching local ARKitScenes task root."""
from __future__ import annotations

from arkitscenes_handoff_common import LOCAL_ROOT, TASK_ID, initialize_local_root, read_json


def main() -> None:
    identity_path = LOCAL_ROOT / "TASK_IDENTITY.json"
    if identity_path.exists():
        assert read_json(identity_path)["task_id"] == TASK_ID
    initialize_local_root()
    print("TASK_IDENTITY_PASS")


if __name__ == "__main__":
    main()
