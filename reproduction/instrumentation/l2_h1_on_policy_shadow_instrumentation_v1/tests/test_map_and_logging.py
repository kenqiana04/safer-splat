from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from append_only_logger import AppendOnlyEvidenceLogger  # noqa: E402
from map_authority import MapAuthorityFreezeError, MapAuthorityFreezer  # noqa: E402


class MapAndLoggingTests(unittest.TestCase):
    def _freeze(self, root: Path):
        (root / "map" / "b.bin").parent.mkdir(parents=True)
        (root / "map" / "b.bin").write_bytes(b"b")
        (root / "map" / "a.bin").write_bytes(b"a")
        freezer = MapAuthorityFreezer()
        manifest = freezer.freeze(
            root=root,
            artifacts=["map"],
            logical_map_name="UNIT_MAP",
            representation_contract="UNIT_ONLY",
            robot_radius=0.015,
            safety_margin=0.0,
            effective_radius=0.015,
            rho_seg=0.0,
        )
        return freezer, manifest

    def test_map_authority_is_stable_sorted_and_one_shot(self):
        with tempfile.TemporaryDirectory() as first_temp, tempfile.TemporaryDirectory() as second_temp:
            first, manifest = self._freeze(Path(first_temp))
            _, equivalent = self._freeze(Path(second_temp))
            self.assertEqual(manifest.map_authority_id, equivalent.map_authority_id)
            self.assertEqual([item.relative_path for item in manifest.artifacts], ["map/a.bin", "map/b.bin"])
            self.assertEqual(first.full_hash_call_count, 1)
            self.assertEqual(manifest.to_record()["per_step_full_map_hash_count"], 0)
            with self.assertRaises(MapAuthorityFreezeError):
                first.freeze(
                    root=Path(first_temp), artifacts=["map"], logical_map_name="UNIT_MAP",
                    representation_contract="UNIT_ONLY", robot_radius=0.015,
                    safety_margin=0.0, effective_radius=0.015, rho_seg=0.0,
                )

    def test_map_content_changes_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, first = self._freeze(root)
            (root / "map" / "a.bin").write_bytes(b"changed")
            second = MapAuthorityFreezer().freeze(
                root=root, artifacts=["map"], logical_map_name="UNIT_MAP",
                representation_contract="UNIT_ONLY", robot_radius=0.015,
                safety_margin=0.0, effective_radius=0.015, rho_seg=0.0,
            )
            self.assertNotEqual(first.map_authority_id, second.map_authority_id)

    def test_logger_is_append_only_and_manifest_is_one_shot(self):
        with tempfile.TemporaryDirectory() as temp:
            logger = AppendOnlyEvidenceLogger(Path(temp))
            logger.append_capture({"payload_sequence_id": 1})
            logger.append_capture({"payload_sequence_id": 2})
            self.assertEqual([row["payload_sequence_id"] for row in logger.read_jsonl(logger.step_capture_path)], [1, 2])
            logger.write_map_manifest_once({"map_authority_id": "m"})
            self.assertEqual(json.loads(logger.map_manifest_path.read_text(encoding="utf-8"))["map_authority_id"], "m")
            with self.assertRaises(FileExistsError):
                logger.write_map_manifest_once({"map_authority_id": "different"})


if __name__ == "__main__":
    unittest.main()
