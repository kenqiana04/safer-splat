"""Task-owned, fail-closed ARKitScenes dataset adapter for official SplaTAM.

The official SplaTAM source has no ARKitScenes dispatch.  This adapter supplies
the existing GradSLAMDataset contract without changing the authority checkout.
It deliberately accepts only a raw Git-blob frozen TRAIN manifest for scene
48018874 and has no code path that reads a HELDOUT frame.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

import cv2
import imageio.v2 as imageio
import numpy as np
import torch

from datasets.gradslam_datasets.basedataset import GradSLAMDataset


SCENE_ID = "48018874"
TRAIN_MANIFEST_SHA256 = "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3"
HELDOUT_TOKEN = "HELDOUT"
BASELINE_MASK = "depth_gt_zero"
CONFIDENCE_MASK = "depth_gt_zero_and_confidence_eq_2"


class ARKitScenesSplaTAMDataset(GradSLAMDataset):
    """Canonical-TRAIN-only ARKitScenes RGB-D adapter.

    The base class performs the frozen resize and depth conversion.  ``__getitem__``
    supplies the CSV's per-frame intrinsic matrix after that same resize.  Official
    SplaTAM's mapper has a static-camera-intrinsic assumption; the loader audit
    records the full per-frame values rather than silently homogenising them.
    """

    def __init__(self, config_dict: dict[str, Any], basedir: str, sequence: str, **kwargs: Any) -> None:
        expected_scene = str(config_dict.get("scene_id", SCENE_ID))
        expected_split = str(config_dict.get("expected_split", "TRAIN")).upper()
        manifest_path = Path(str(config_dict["manifest_path"])).resolve()
        asset_root = Path(str(config_dict["asset_root"])).resolve()
        expected_sha256 = str(config_dict.get("manifest_sha256", TRAIN_MANIFEST_SHA256)).lower()
        mask_mode = str(config_dict.get("depth_mask_mode", BASELINE_MASK))

        if expected_scene != SCENE_ID or str(sequence) != SCENE_ID:
            raise ValueError(f"adapter only accepts scene {SCENE_ID}")
        if expected_split != "TRAIN":
            raise ValueError("adapter refuses every non-TRAIN split")
        if mask_mode not in (BASELINE_MASK, CONFIDENCE_MASK):
            raise ValueError(f"unsupported frozen depth mask: {mask_mode}")
        if not manifest_path.is_file() or not asset_root.is_dir():
            raise FileNotFoundError("canonical manifest or ARKitScenes asset root unavailable")
        actual_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if actual_sha256 != expected_sha256 or expected_sha256 != TRAIN_MANIFEST_SHA256:
            raise ValueError("noncanonical TRAIN manifest raw-byte identity")

        with manifest_path.open("r", encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        if len(records) != 214:
            raise ValueError(f"expected 214 canonical TRAIN rows, received {len(records)}")
        if not records:
            raise ValueError("empty canonical TRAIN manifest")
        for row in records:
            if row.get("video_id") != SCENE_ID:
                raise ValueError("manifest contains an unauthorized scene")
            if row.get("split", "").upper() != "TRAIN":
                raise ValueError("manifest contains HELDOUT or non-TRAIN data")
            if HELDOUT_TOKEN in " ".join(row.values()).upper():
                raise ValueError("manifest contains a HELDOUT token")

        self.manifest_path = manifest_path
        self.asset_root = asset_root
        self.manifest_sha256 = actual_sha256
        self.depth_mask_mode = mask_mode
        self.records = records
        self.confidence_paths: list[Path] = []
        first = records[0]
        config = {
            "dataset_name": "arkitscenes",
            "camera_params": {
                "png_depth_scale": 1000.0,
                "image_height": int(first["height"]),
                "image_width": int(first["width"]),
                "fx": float(first["fx"]),
                "fy": float(first["fy"]),
                "cx": float(first["cx"]),
                "cy": float(first["cy"]),
            },
        }
        super().__init__(config, **kwargs)

    def _resolve_asset(self, relative_path: str) -> Path:
        candidate = (self.asset_root / relative_path).resolve()
        try:
            candidate.relative_to(self.asset_root)
        except ValueError as exc:
            raise ValueError("asset path escapes the frozen ARKitScenes root") from exc
        if not candidate.is_file():
            raise FileNotFoundError(f"missing canonical asset: {relative_path}")
        return candidate

    @staticmethod
    def _c2w_from_row(row: dict[str, str]) -> torch.Tensor:
        pose = np.array(
            [[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)],
            dtype=np.float32,
        )
        if not np.isfinite(pose).all() or not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6):
            raise ValueError("invalid canonical Apple C2W pose")
        return torch.from_numpy(pose)

    def get_filepaths(self):
        color_paths: list[str] = []
        depth_paths: list[str] = []
        self.tmp_poses: list[torch.Tensor] = []
        self.confidence_paths = []
        for row in self.records:
            color_paths.append(str(self._resolve_asset(row["rgb"])))
            depth_paths.append(str(self._resolve_asset(row["depth"])))
            self.confidence_paths.append(self._resolve_asset(row["confidence"]))
            self._resolve_asset(row["intrinsics"])
            self.tmp_poses.append(self._c2w_from_row(row))
        return color_paths, depth_paths, None

    def load_poses(self):
        return self.tmp_poses

    def _record_for_retained_index(self, index: int) -> dict[str, str]:
        source_index = int(self.retained_inds[index].item())
        return self.records[source_index]

    def _intrinsics_for_record(self, row: dict[str, str], device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        k = torch.eye(4, device=device, dtype=dtype)
        k[0, 0] = float(row["fx"]) * self.width_downsample_ratio
        k[1, 1] = float(row["fy"]) * self.height_downsample_ratio
        k[0, 2] = float(row["cx"]) * self.width_downsample_ratio
        k[1, 2] = float(row["cy"]) * self.height_downsample_ratio
        return k

    def __getitem__(self, index: int):
        color, depth, _static_intrinsics, pose = super().__getitem__(index)
        row = self._record_for_retained_index(index)
        intrinsics = self._intrinsics_for_record(row, device=depth.device, dtype=depth.dtype)
        if self.depth_mask_mode == CONFIDENCE_MASK:
            source_index = int(self.retained_inds[index].item())
            confidence = np.asarray(imageio.imread(self.confidence_paths[source_index]))
            confidence = cv2.resize(
                confidence,
                (self.desired_width, self.desired_height),
                interpolation=cv2.INTER_NEAREST,
            )
            mask = torch.from_numpy(confidence == 2).to(device=depth.device)
            depth = depth.clone()
            depth[~mask.unsqueeze(-1)] = 0
        return color, depth, intrinsics, pose

    def canonical_frame_identity(self, index: int) -> dict[str, str]:
        """Return only frozen identity fields for evidence/reporting."""
        row = self._record_for_retained_index(index)
        return {
            key: row[key]
            for key in ("video_id", "timestamp", "rgb", "depth", "confidence", "intrinsics", "split")
        }
