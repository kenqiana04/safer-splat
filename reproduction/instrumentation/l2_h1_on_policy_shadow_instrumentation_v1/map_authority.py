"""Run-start content-addressed authority for static map artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from canonical_hash import semantic_sha256


class MapAuthorityFreezeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MapArtifactRecord:
    relative_path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class MapAuthorityManifest:
    schema_version: str
    logical_map_name: str
    artifacts: tuple[MapArtifactRecord, ...]
    representation_contract: str
    robot_radius: float
    safety_margin: float
    effective_radius: float
    rho_seg: float
    map_authority_id: str

    def semantic_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "logical_map_name": self.logical_map_name,
            "artifacts": tuple(
                {"relative_path": item.relative_path, "size": item.size, "sha256": item.sha256}
                for item in self.artifacts
            ),
            "representation_contract": self.representation_contract,
            "robot_radius": self.robot_radius,
            "safety_margin": self.safety_margin,
            "effective_radius": self.effective_radius,
            "rho_seg": self.rho_seg,
        }

    def to_record(self) -> dict:
        value = self.semantic_dict()
        value["map_authority_id"] = self.map_authority_id
        value["full_map_hash_call_count_per_run"] = 1
        value["per_step_full_map_hash_count"] = 0
        return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class MapAuthorityFreezer:
    """Single-use freezer: a second full-map freeze is an error."""

    def __init__(self) -> None:
        self.full_hash_call_count = 0
        self._manifest: MapAuthorityManifest | None = None

    def freeze(
        self,
        *,
        root: Path,
        artifacts: Iterable[Path | str],
        logical_map_name: str,
        representation_contract: str,
        robot_radius: float,
        safety_margin: float,
        effective_radius: float,
        rho_seg: float,
    ) -> MapAuthorityManifest:
        if self._manifest is not None or self.full_hash_call_count != 0:
            raise MapAuthorityFreezeError("full map authority may be frozen exactly once per run")
        self.full_hash_call_count += 1
        try:
            root = root.resolve(strict=True)
            files: dict[str, Path] = {}
            for item in artifacts:
                path = (root / item).resolve(strict=True) if not Path(item).is_absolute() else Path(item).resolve(strict=True)
                try:
                    path.relative_to(root)
                except ValueError as exc:
                    raise MapAuthorityFreezeError("map artifact escapes the declared root") from exc
                if path.is_dir():
                    candidates = (candidate for candidate in path.rglob("*") if candidate.is_file())
                elif path.is_file():
                    candidates = (path,)
                else:
                    raise MapAuthorityFreezeError(f"unsupported map artifact: {path}")
                for candidate in candidates:
                    relative = candidate.relative_to(root).as_posix()
                    files[relative] = candidate
            if not files:
                raise MapAuthorityFreezeError("no map artifacts were found")
            records = tuple(
                MapArtifactRecord(relative, files[relative].stat().st_size, _file_sha256(files[relative]))
                for relative in sorted(files)
            )
            semantic = {
                "schema_version": "MAP_AUTHORITY_MANIFEST_V1",
                "logical_map_name": str(logical_map_name),
                "artifacts": tuple(
                    {"relative_path": item.relative_path, "size": item.size, "sha256": item.sha256}
                    for item in records
                ),
                "representation_contract": str(representation_contract),
                "robot_radius": float(robot_radius),
                "safety_margin": float(safety_margin),
                "effective_radius": float(effective_radius),
                "rho_seg": float(rho_seg),
            }
            self._manifest = MapAuthorityManifest(
                schema_version=semantic["schema_version"],
                logical_map_name=semantic["logical_map_name"],
                artifacts=records,
                representation_contract=semantic["representation_contract"],
                robot_radius=semantic["robot_radius"],
                safety_margin=semantic["safety_margin"],
                effective_radius=semantic["effective_radius"],
                rho_seg=semantic["rho_seg"],
                map_authority_id=semantic_sha256(semantic),
            )
            return self._manifest
        except MapAuthorityFreezeError:
            raise
        except Exception as exc:
            raise MapAuthorityFreezeError(str(exc)) from exc

    @property
    def manifest(self) -> MapAuthorityManifest | None:
        return self._manifest
