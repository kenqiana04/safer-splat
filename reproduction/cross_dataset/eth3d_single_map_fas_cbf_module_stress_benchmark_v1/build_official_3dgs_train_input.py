#!/usr/bin/env python3
"""Build a read-only, TRAIN-only COLMAP adapter for official 3DGS.

The frozen ETH3D contract keeps images in camera-specific subdirectories while
the official loader resolves COLMAP image names by basename.  This adapter makes
one flat directory of symlinks without copying, deleting, filtering, or decoding
any image.  It never traverses EVAL_ORACLE_ROOT.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_colmap_image_names(path: Path) -> list[str]:
    names: list[str] = []
    with path.open("rb") as stream:
        (count,) = struct.unpack("<Q", stream.read(8))
        for _ in range(count):
            header = stream.read(64)
            if len(header) != 64:
                raise RuntimeError("truncated COLMAP images.bin header")
            name_bytes = bytearray()
            while True:
                byte = stream.read(1)
                if byte == b"":
                    raise RuntimeError("truncated COLMAP image name")
                if byte == b"\x00":
                    break
                name_bytes.extend(byte)
            names.append(name_bytes.decode("utf-8"))
            (points_2d,) = struct.unpack("<Q", stream.read(8))
            stream.seek(points_2d * 24, os.SEEK_CUR)
    return names


def read_colmap_image_names_text(path: Path) -> list[str]:
    records = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(records) % 2:
        raise RuntimeError("COLMAP images.txt must contain image/point-line pairs")
    names: list[str] = []
    for image_record in records[0::2]:
        fields = image_record.split(maxsplit=9)
        if len(fields) != 10:
            raise RuntimeError(f"invalid COLMAP image record: {image_record[:120]}")
        names.append(fields[9])
    return names


def rewrite_colmap_image_names_text(
    source: Path, destination: Path, renamed: dict[str, str]
) -> None:
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    record_index = 0
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            output.append(line)
            continue
        if record_index % 2 == 0:
            newline = "\n" if line.endswith("\n") else ""
            content = line[:-1] if newline else line
            prefix, old_name = content.rsplit(maxsplit=1)
            output.append(f"{prefix} {renamed[old_name]}{newline}")
        else:
            output.append(line)
        record_index += 1
    destination.write_text("".join(output), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-root", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--identity-out", type=Path, required=True)
    args = parser.parse_args()

    train_root = args.train_root.resolve(strict=True)
    if "EVAL_ORACLE_ROOT" in train_root.parts:
        raise RuntimeError("TRAIN adapter may not use EVAL_ORACLE_ROOT")
    images_root = train_root / "images"
    sparse_root = train_root / "sparse" / "0"
    images_bin = sparse_root / "images.bin"
    images_txt = sparse_root / "images.txt"
    if images_bin.is_file():
        image_model_path = images_bin
        names = read_colmap_image_names(images_bin)
        image_model_format = "binary"
    elif images_txt.is_file():
        image_model_path = images_txt
        names = read_colmap_image_names_text(images_txt)
        image_model_format = "text"
    else:
        raise RuntimeError("neither COLMAP images.bin nor images.txt exists")

    candidates: dict[str, list[Path]] = {}
    for path in sorted(images_root.rglob("*")):
        if path.is_file():
            candidates.setdefault(path.name, []).append(path)

    missing: list[str] = []
    ambiguous: list[str] = []
    selected: dict[str, Path] = {}
    renamed: dict[str, str] = {}
    for colmap_name in names:
        exact = images_root / Path(colmap_name)
        matches = [exact] if exact.is_file() else candidates.get(Path(colmap_name).name, [])
        target_name = Path(colmap_name).as_posix().replace("/", "__")
        if not matches:
            missing.append(colmap_name)
        elif len(matches) != 1:
            ambiguous.append(colmap_name)
        elif target_name in selected:
            ambiguous.append(colmap_name)
        else:
            selected[target_name] = matches[0]
            renamed[colmap_name] = target_name
    if missing or ambiguous or len(selected) != len(names):
        raise RuntimeError(
            f"adapter mapping failed: images={len(names)} selected={len(selected)} "
            f"missing={len(missing)} ambiguous={len(ambiguous)}"
        )

    if args.adapter_root.exists():
        raise RuntimeError(f"adapter root already exists: {args.adapter_root}")
    flat_images = args.adapter_root / "images"
    flat_images.mkdir(parents=True)
    adapted_sparse = args.adapter_root / "sparse" / "0"
    adapted_sparse.mkdir(parents=True)
    for filename in ("cameras.bin", "cameras.txt", "points3D.bin", "points3D.txt"):
        source = sparse_root / filename
        if source.is_file():
            os.symlink(source.resolve(), adapted_sparse / filename)
    if image_model_format == "text":
        rewrite_colmap_image_names_text(
            images_txt, adapted_sparse / "images.txt", renamed
        )
    else:
        os.symlink(images_bin.resolve(), adapted_sparse / "images.bin")
    for target_name, source in selected.items():
        os.symlink(source.resolve(), flat_images / target_name)

    image_model_sha = sha256(image_model_path)
    ordered_targets = [str(selected[renamed.get(name, Path(name).name)].resolve()) for name in names]
    mapping_sha = hashlib.sha256(
        ("\n".join(f"{renamed.get(name, Path(name).name)}\t{target}" for name, target in zip(names, ordered_targets)) + "\n").encode("utf-8")
    ).hexdigest()
    record = {
        "schema_version": 1,
        "frontend": "OFFICIAL_3DGS_COLMAP_RGB_ONLY",
        "train_root": str(train_root),
        "adapter_root": str(args.adapter_root.resolve()),
        "colmap_image_count": len(names),
        "flat_symlink_count": len(selected),
        "missing_count": len(missing),
        "ambiguous_count": len(ambiguous),
        "image_model_format": image_model_format,
        "image_model_path": str(image_model_path),
        "image_model_sha256": image_model_sha,
        "adapted_image_model_sha256": sha256(
            adapted_sparse / ("images.txt" if image_model_format == "text" else "images.bin")
        ),
        "image_name_rewrite_count": len(renamed) if image_model_format == "text" else 0,
        "camera_parameter_change_count": 0,
        "pose_change_count": 0,
        "point_change_count": 0,
        "mapping_sha256": mapping_sha,
        "reference_access_count": 0,
        "heldout_access_count": 0,
        "frame_deletion_count": 0,
        "image_decode_count": 0,
    }
    args.identity_out.parent.mkdir(parents=True, exist_ok=True)
    args.identity_out.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("OFFICIAL_3DGS_TRAIN_INPUT_ADAPTER_PASS")
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
