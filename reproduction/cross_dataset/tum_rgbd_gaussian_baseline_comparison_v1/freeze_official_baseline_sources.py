"""Freeze official archive identities without mutating either source tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCES = {
    "SplaTAM": {
        "remote_url": "https://github.com/spla-tam/SplaTAM.git",
        "commit": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
        "archive_sha256": "f62547bc3a4dd84f499d216b9bca5d293bf5f5ecb24f742ef0b8a51fb53c2bfa",
        "submodules": {"diff-gaussian-rasterization-w-depth.git": "cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110"},
        "license": "MIT",
    },
    "Gaussian-SLAM": {
        "remote_url": "https://github.com/VladimirYugay/Gaussian-SLAM.git",
        "commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
        "archive_sha256": "0833f175805899d22b18a4cb1fbcf758a937af96e2914b2027409dd9bc16acff",
        "submodules": {},
        "license": "Apache-2.0",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_manifest(root: Path) -> str:
    records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        records.append(f"{sha256(path)}  {path.relative_to(root).as_posix()}")
    return hashlib.sha256("\n".join(records).encode("utf-8")).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    repos = args.root / "repos"
    cache = args.root / "cache"
    names = {"SplaTAM": "SplaTAM_official_archive", "Gaussian-SLAM": "Gaussian-SLAM_official_archive"}
    out = {"status": "PASS", "source_mode": "official_codeload_archives", "sources": {}}
    for key, dirname in names.items():
        entry = dict(SOURCES[key])
        repo = repos / dirname
        archive = cache / ("SplaTAM-da6bbcd.tar.gz" if key == "SplaTAM" else "Gaussian-SLAM-eaec10d.tar.gz")
        if not repo.is_dir() or not archive.is_file():
            raise RuntimeError(f"SOURCE_ARCHIVE_MISSING:{key}")
        if sha256(archive) != entry.pop("archive_sha256"):
            raise RuntimeError(f"ARCHIVE_HASH_MISMATCH:{key}")
        entry.update({
            "archive_path": str(archive), "archive_verified": True,
            "source_path": str(repo), "source_manifest_sha256": tree_manifest(repo),
            "dirty": False, "git_worktree": "not_applicable_official_archive",
            "license_file_present": (repo / "LICENSE").is_file(),
        })
        out["sources"][key] = entry
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
