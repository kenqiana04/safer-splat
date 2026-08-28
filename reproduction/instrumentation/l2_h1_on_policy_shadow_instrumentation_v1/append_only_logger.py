"""Append-only JSONL evidence logs and one-shot map manifest writer."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class AppendOnlyEvidenceLogger:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.step_capture_path = self.root / "step_capture_log.jsonl"
        self.shadow_result_path = self.root / "shadow_certificate_result_log.jsonl"
        self.health_path = self.root / "instrumentation_health_log.jsonl"
        self.map_manifest_path = self.root / "map_authority_manifest.json"
        self._lock = threading.Lock()
        for path in (self.step_capture_path, self.shadow_result_path, self.health_path):
            path.touch(exist_ok=True)

    @staticmethod
    def _line(record: dict[str, Any]) -> str:
        return json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n"

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        with self._lock, path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(self._line(record))
            handle.flush()

    def append_capture(self, record: dict[str, Any]) -> None:
        self._append(self.step_capture_path, record)

    def append_result(self, record: dict[str, Any]) -> None:
        self._append(self.shadow_result_path, record)

    def append_health(self, record: dict[str, Any]) -> None:
        self._append(self.health_path, record)

    def write_map_manifest_once(self, record: dict[str, Any]) -> None:
        with self._lock:
            if self.map_manifest_path.exists():
                raise FileExistsError("map authority manifest is one-shot and immutable")
            self.map_manifest_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
