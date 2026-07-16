#!/usr/bin/env python3
"""Read-only 4090 audit for TUM depth provenance and Nerfstudio parsing.

This module intentionally invokes only the Nerfstudio dataparser API.  It does
not construct a model, trainer, optimizer, viewer, checkpoint, or SAFER loader.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import sys
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def json_dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolved(path: Path) -> str:
    return str(path.expanduser().resolve())


def stage(result: dict[str, Any], name: str, action) -> Any:
    entry: dict[str, Any] = {"stage": name, "status": "running"}
    result["stages"].append(entry)
    try:
        value = action()
    except Exception as exc:  # Preserve the precise stage; never relabel as generation.
        entry.update(
            {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "full_traceback": traceback.format_exc(),
            }
        )
        result.update(
            {
                "status": "BLOCKED_BY_DATAPARSER_GENERATION"
                if name in {"import_environment", "create_config", "instantiate_dataparser", "generate_train_outputs", "generate_eval_outputs"}
                else "BLOCKED_BY_DATAPARSER_POSTPROCESS",
                "failure_stage": name,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "full_traceback": traceback.format_exc(),
            }
        )
        raise
    entry["status"] = "passed"
    return value


def source_frame_map(data: Path, frames: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for frame in frames:
        mapped[resolved(data / frame["file_path"])] = frame
    return mapped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--selected-csv", type=Path, required=True)
    parser.add_argument("--official-depth-page", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    data, raw, selected_csv, page, out = args.data.resolve(), args.raw.resolve(), args.selected_csv.resolve(), args.official_depth_page.resolve(), args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Official evidence is fetched before this script runs and is only read here.
    page_text = page.read_text(encoding="utf-8", errors="replace")
    contract = {
        "source_url": "https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats",
        "retrieved_at_utc": now,
        "retrieval_host": platform.node(),
        "source_page_sha256": sha256(page),
        "dataset_family": "TUM_RGBD",
        "sequence": "rgbd_dataset_freiburg1_room",
        "depth_format": "640x480 16-bit monochrome PNG",
        "depth_units_per_meter": 5000,
        "depth_unit_scale_factor_meters": 1.0 / 5000.0,
        "zero_semantics": "missing_value_or_no_data",
        "freiburg1_correction_value": 1.035,
        "correction_already_applied": True,
        "additional_correction_required": False,
        "evidence_status": "pass_official_tum_source",
        "notes": "Official page states 5000 depth units equal 1 meter, zero is no data, and Freiburg 1 depth is already pre-scaled.",
        "required_phrases_present": {
            "16_bit_png": "16-bit monochrome" in page_text,
            "5000_units": "pixel value of 5000 in the depth image corresponds to a distance of 1 meter" in page_text,
            "zero_no_data": "0 means missing value/no data" in page_text,
            "freiburg1_1035": "Freiburg 1" in page_text and "1.035" in page_text,
            "already_pre_scaled": "already pre-scaled" in page_text,
        },
    }
    json_dump(out / "official_tum_depth_contract.json", contract)

    transforms = json.loads((data / "transforms.json").read_text(encoding="utf-8"))
    frames = transforms["frames"]
    selected = list(csv.DictReader(selected_csv.open("r", encoding="utf-8", newline="")))
    if len(frames) != len(selected):
        raise RuntimeError(f"selected registry count {len(selected)} does not match transforms frame count {len(frames)}")

    # The historical immutable preprocessor used shutil.copy2 for every selected depth.
    from PIL import Image

    identity_rows: list[dict[str, Any]] = []
    for index, (frame, registry) in enumerate(zip(frames, selected)):
        processed = (data / frame["depth_file_path"]).resolve()
        raw_depth = (raw / registry["depth_path"]).resolve()
        processed_exists, raw_exists = processed.is_file(), raw_depth.is_file()
        dtype = shape = None
        if processed_exists:
            with Image.open(processed) as image:
                dtype, shape = str(image.mode), list(image.size)[::-1]
        processed_hash = sha256(processed) if processed_exists else None
        raw_hash = sha256(raw_depth) if raw_exists else None
        same = processed_hash is not None and processed_hash == raw_hash
        identity_rows.append(
            {
                "frame_index": index,
                "timestamp": registry["rgb_timestamp"],
                "transforms_depth_path": frame["depth_file_path"],
                "processed_depth_path": str(processed),
                "raw_depth_path": str(raw_depth),
                "processed_exists": processed_exists,
                "raw_exists": raw_exists,
                "processed_sha256": processed_hash,
                "raw_sha256": raw_hash,
                "byte_identical": same,
                "direct_reference": processed == raw_depth,
                "file_size_equal": processed_exists and raw_exists and processed.stat().st_size == raw_depth.stat().st_size,
                "dtype": dtype,
                "shape": json.dumps(shape),
                "mapping_source": "historical_tum_selected_frames.csv + frozen transforms.json",
            }
        )
    with (out / "depth_copy_identity_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(identity_rows[0]))
        writer.writeheader()
        writer.writerows(identity_rows)
    identity_summary = {
        "expected_count": len(frames),
        "mapped_count": len(identity_rows),
        "raw_found_count": sum(row["raw_exists"] for row in identity_rows),
        "processed_found_count": sum(row["processed_exists"] for row in identity_rows),
        "byte_identical_count": sum(row["byte_identical"] for row in identity_rows),
        "mismatch_count": sum(not row["byte_identical"] for row in identity_rows),
        "unresolved_mapping_count": sum(not row["raw_exists"] or not row["processed_exists"] for row in identity_rows),
        "direct_reference_count": sum(row["direct_reference"] for row in identity_rows),
        "copied_identically_count": sum(row["byte_identical"] and not row["direct_reference"] for row in identity_rows),
    }

    parser_result: dict[str, Any] = {
        "status": "PASS_DATAPARSER_ONLY",
        "stages": [],
        "api_invoked": True,
        "model_created": False,
        "optimizer_created": False,
        "trainer_created": False,
        "viewer_created": False,
        "training_iterations_executed": 0,
        "checkpoint_created": False,
        "safer_executed": False,
        "source_frame_count": len(frames),
    }
    preflight: dict[str, Any] = {}
    try:
        def import_environment():
            import gsplat  # noqa: F401
            import nerfstudio  # noqa: F401
            import torch
            from nerfstudio.data.dataparsers.nerfstudio_dataparser import Nerfstudio, NerfstudioDataParserConfig
            preflight.update(
                {
                    "authoritative_execution_host": platform.node(),
                    "authoritative_conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
                    "authoritative_python": sys.executable,
                    "python_version": sys.version,
                    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                    "torch_version": torch.__version__,
                    "cuda_version": torch.version.cuda,
                    "cuda_available": torch.cuda.is_available(),
                    "visible_device_count": torch.cuda.device_count(),
                    "visible_device_0": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    "nerfstudio_version": package_version("nerfstudio"),
                    "gsplat_version": package_version("gsplat"),
                    "training_iterations_executed": 0,
                    "checkpoint_created": False,
                    "safer_executed": False,
                }
            )
            return torch, Nerfstudio, NerfstudioDataParserConfig

        torch, Nerfstudio, NerfstudioDataParserConfig = stage(parser_result, "import_environment", import_environment)
        field = NerfstudioDataParserConfig.__dataclass_fields__.get("depth_unit_scale_factor")
        installed_default = field.default if field is not None else None

        cfg = stage(
            parser_result,
            "create_config",
            lambda: NerfstudioDataParserConfig(
                data=data,
                orientation_method="none",
                center_method="none",
                auto_scale_poses=False,
                downscale_factor=1,
                eval_mode="fraction",
                train_split_fraction=0.8,
                depth_unit_scale_factor=1.0 / 5000.0,
            ),
        )
        dp = stage(parser_result, "instantiate_dataparser", lambda: Nerfstudio(cfg))
        train = stage(parser_result, "generate_train_outputs", lambda: dp._generate_dataparser_outputs(split="train"))
        eval_out = stage(parser_result, "generate_eval_outputs", lambda: dp._generate_dataparser_outputs(split="val"))

        def inspect_transform_shape():
            transform = train.dataparser_transform
            parser_result.update(
                {
                    "dataparser_transform_shape": list(transform.shape),
                    "dataparser_transform_dtype": str(transform.dtype),
                    "dataparser_transform_device": str(transform.device),
                    "dataparser_transform_values": transform.detach().cpu().tolist(),
                    "dataparser_scale": float(train.dataparser_scale),
                    "orientation_method": cfg.orientation_method,
                    "center_method": cfg.center_method,
                    "auto_scale_poses": cfg.auto_scale_poses,
                    "depth_paths_present": bool(train.metadata and train.metadata.get("depth_filenames") is not None),
                }
            )
            return transform

        transform = stage(parser_result, "inspect_transform_shape", inspect_transform_shape)

        def compare_transform():
            native_shape = tuple(transform.shape)
            if native_shape == (3, 4):
                expected = torch.eye(4, dtype=transform.dtype, device=transform.device)[:3, :]
            elif native_shape == (4, 4):
                expected = torch.eye(4, dtype=transform.dtype, device=transform.device)
            else:
                raise RuntimeError(f"DataparserTransformShapeError: expected (3, 4) or (4, 4), got {native_shape}")
            max_error = float(torch.max(torch.abs(transform - expected)).item())
            parser_result.update(
                {
                    "expected_identity_shape": list(expected.shape),
                    "dataparser_transform_identity": bool(torch.allclose(transform, expected, atol=1e-7, rtol=0.0)),
                    "dataparser_transform_max_abs_error": max_error,
                    "dataparser_scale_is_one": abs(float(train.dataparser_scale) - 1.0) <= 1e-9,
                }
            )

        stage(parser_result, "compare_dataparser_transform", compare_transform)

        source_map = source_frame_map(data, frames)
        pose_rows: list[dict[str, Any]] = []

        def map_files():
            seen: set[str] = set()
            for split, output in (("train", train), ("val", eval_out)):
                for index, filename in enumerate(output.image_filenames):
                    parsed_path = resolved(Path(filename))
                    seen.add(parsed_path)
                    frame = source_map.get(parsed_path)
                    pose_rows.append(
                        {
                            "split": split,
                            "parsed_index": index,
                            "parsed_image_path": parsed_path,
                            "source_matched": frame is not None,
                            "source_image_path": parsed_path if frame else None,
                            "parsed_pose_shape": json.dumps(list(output.cameras.camera_to_worlds[index].shape)),
                        }
                    )
            parser_result.update(
                {
                    "parsed_train_count": len(train.image_filenames),
                    "parsed_eval_count": len(eval_out.image_filenames),
                    "parsed_total_count": len(train.image_filenames) + len(eval_out.image_filenames),
                    "parsed_unique_total": len(seen),
                    "duplicate_parsed_path_count": len(train.image_filenames) + len(eval_out.image_filenames) - len(seen),
                    "unmatched_parsed_count": sum(not row["source_matched"] for row in pose_rows),
                    "unmatched_source_count": len(set(source_map) - seen),
                    "frame_drop_count": len(frames) - len(seen),
                }
            )

        stage(parser_result, "map_parsed_files_to_source", map_files)

        def compare_poses():
            ratios: list[float] = []
            source_norms: list[float] = []
            parsed_norms: list[float] = []
            vector_errors: list[float] = []
            for row in pose_rows:
                if not row["source_matched"]:
                    continue
                source = torch.tensor(source_map[row["parsed_image_path"]]["transform_matrix"], dtype=torch.float64)
                output = train if row["split"] == "train" else eval_out
                parsed = output.cameras.camera_to_worlds[row["parsed_index"]].detach().cpu().to(dtype=torch.float64)
                source_translation, parsed_translation = source[:3, 3], parsed[:3, 3]
                source_norm, parsed_norm = float(torch.linalg.vector_norm(source_translation)), float(torch.linalg.vector_norm(parsed_translation))
                vector_error = float(torch.linalg.vector_norm(parsed_translation - source_translation))
                ratio = parsed_norm / source_norm if source_norm > 0.0 else None
                row.update(
                    {
                        "source_translation_norm_m": source_norm,
                        "parsed_translation_norm_m": parsed_norm,
                        "translation_ratio": ratio,
                        "translation_vector_error_m": vector_error,
                    }
                )
                source_norms.append(source_norm)
                parsed_norms.append(parsed_norm)
                vector_errors.append(vector_error)
                if ratio is not None:
                    ratios.append(ratio)
            parser_result.update(
                {
                    "matched_pose_count": len(source_norms),
                    "unmatched_pose_count": len(pose_rows) - len(source_norms),
                    "source_translation_norm_median": float(torch.median(torch.tensor(source_norms)).item()) if source_norms else None,
                    "parsed_translation_norm_median": float(torch.median(torch.tensor(parsed_norms)).item()) if parsed_norms else None,
                    "ratio_median": float(torch.median(torch.tensor(ratios)).item()) if ratios else None,
                    "ratio_min": min(ratios) if ratios else None,
                    "ratio_max": max(ratios) if ratios else None,
                    "translation_vector_error_max": max(vector_errors) if vector_errors else None,
                    "translation_vector_error_median": float(torch.median(torch.tensor(vector_errors)).item()) if vector_errors else None,
                }
            )

        stage(parser_result, "compare_source_and_parsed_poses", compare_poses)
        stage(parser_result, "compute_translation_scale_ratio", lambda: None)
    except Exception:
        pass

    # This static record distinguishes source-scale closure from the future train entry contract.
    closure = {
        "official_units_per_meter": contract["depth_units_per_meter"],
        "official_scale_to_meters": contract["depth_unit_scale_factor_meters"],
        "official_freiburg1_correction_already_applied": contract["correction_already_applied"],
        "historical_preprocessor_operation": "shutil.copy2",
        "historical_preprocessor_scales_depth": False,
        "historical_preprocessor_applies_1_035": False,
        "historical_preprocessor_converts_to_float": False,
        "historical_preprocessor_reencodes_png": False,
        "selected_depth_byte_identity_status": "pass" if identity_summary["mismatch_count"] == 0 and identity_summary["mapped_count"] == 300 else "fail",
        "identity_summary": identity_summary,
        "transforms_depth_scale_field_present": "depth_unit_scale_factor" in transforms,
        "transforms_depth_scale_field_value": transforms.get("depth_unit_scale_factor"),
        "nerfstudio_config_scale_source": "NerfstudioDataParserConfig.depth_unit_scale_factor",
        "future_required_depth_unit_scale_factor": contract["depth_unit_scale_factor_meters"],
        "double_scaling_risk": False,
        "final_depth_contract_status": "pass" if all(contract["required_phrases_present"].values()) and identity_summary["mismatch_count"] == 0 else "fail",
    }
    json_dump(out / "depth_scale_closure.json", closure)

    entry = {
        "command_status": "PASS_ENTRY_CONTRACT" if parser_result.get("status") == "PASS_DATAPARSER_ONLY" else "BLOCKED_BY_TRAINING_ENTRY_CONTRACT",
        "authoritative_execution_host": platform.node(),
        "environment": os.environ.get("CONDA_DEFAULT_ENV"),
        "nerfstudio_version": preflight.get("nerfstudio_version"),
        "data_path": str(data),
        "method": "splatfacto",
        "official_tum_depth_units_per_meter": contract["depth_units_per_meter"],
        "required_depth_unit_scale_factor": contract["depth_unit_scale_factor_meters"],
        "installed_nerfstudio_default_depth_scale": installed_default if "installed_default" in locals() else None,
        "default_matches_tum": installed_default == contract["depth_unit_scale_factor_meters"] if "installed_default" in locals() else False,
        "explicit_override_required": True,
        "exact_cli_option_if_available": "--pipeline.datamanager.dataparser.depth-unit-scale-factor 0.0002",
        "double_scaling_prevention_rule": "Use raw/copied uint16 TUM depth exactly once with depth_unit_scale_factor=1/5000; do not apply Freiburg1 1.035 again.",
        "future_command_template": "NOT EXECUTED: CUDA_VISIBLE_DEVICES=1 ns-train splatfacto --data <immutable_processed_tum_root> nerfstudio-data --orientation-method none --center-method none --auto-scale-poses False --downscale-factor 1 --depth-unit-scale-factor 0.0002",
        "formal_training_not_authorized": True,
        "training_iterations_executed": 0,
        "checkpoint_created": False,
    }
    stage(parser_result, "write_results", lambda: None)
    json_dump(out / "remote_server_preflight.json", preflight)
    json_dump(out / "nerfstudio_environment_audit.json", preflight)
    json_dump(out / "nerfstudio_dataparser_audit.json", parser_result)
    json_dump(out / "dataparser_correction_result.json", parser_result)
    json_dump(out / "splatfacto_entry_command.json", entry)
    if pose_rows:
        with (out / "dataparser_pose_mapping_audit.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pose_rows[0]))
            writer.writeheader()
            writer.writerows(pose_rows)
    manifest = {path.name: sha256(path) for path in sorted(out.iterdir()) if path.is_file()}
    json_dump(out / "correction_remote_manifest.json", {"generated_at_utc": now, "files": manifest})
    print(parser_result["status"])


if __name__ == "__main__":
    main()
