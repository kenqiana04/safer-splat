"""Fail-closed ARKitScenes M1 loader for the frozen SplaTAM qualification.

Only the canonical 214-row TRAIN manifest for scene 48018874 is accepted.
Metric depth is retained exactly when depth > 0 and Apple confidence >= 1.
No HELDOUT manifest is reachable through this mapper adapter.
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
MASK_CONTRACT = "DEPTH_GT_ZERO_AND_CONFIDENCE_GE1"


class ARKitScenesM1SplaTAMDataset(GradSLAMDataset):
    """Canonical TRAIN-only metric RGB-D dataset with the frozen M1 mask."""

    def __init__(self, config_dict: dict[str, Any], basedir: str, sequence: str, **kwargs: Any) -> None:
        manifest_path = Path(str(config_dict["manifest_path"])).resolve()
        asset_root = Path(str(config_dict["asset_root"])).resolve()
        if str(sequence) != SCENE_ID or str(config_dict.get("scene_id")) != SCENE_ID:
            raise ValueError("adapter accepts only frozen scene 48018874")
        if str(config_dict.get("expected_split", "")).upper() != "TRAIN":
            raise ValueError("adapter refuses non-TRAIN inputs")
        if str(config_dict.get("depth_mask_contract")) != MASK_CONTRACT:
            raise ValueError("adapter requires frozen M1 depth mask contract")
        if not manifest_path.is_file() or not asset_root.is_dir():
            raise FileNotFoundError("frozen manifest or asset root unavailable")
        raw = manifest_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != TRAIN_MANIFEST_SHA256:
            raise ValueError("noncanonical TRAIN manifest raw-byte identity")
        with manifest_path.open("r", encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        if len(records) != 214:
            raise ValueError(f"expected 214 TRAIN rows, received {len(records)}")
        for row in records:
            if row.get("video_id") != SCENE_ID or row.get("split", "").upper() != "TRAIN":
                raise ValueError("manifest contains unauthorized scene or split")

        self.manifest_path = manifest_path
        self.asset_root = asset_root
        self.records = records
        self.confidence_paths: list[Path] = []
        first = records[0]
        config = {
            "dataset_name": "arkitscenes_m1",
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

    def _asset(self, relative: str) -> Path:
        candidate = (self.asset_root / relative).resolve()
        try:
            candidate.relative_to(self.asset_root)
        except ValueError as exc:
            raise ValueError("asset path escapes frozen root") from exc
        if not candidate.is_file():
            raise FileNotFoundError(f"missing frozen asset: {relative}")
        return candidate

    @staticmethod
    def _pose(row: dict[str, str]) -> torch.Tensor:
        pose = np.array([[float(row[f"c2w_{i}{j}"]) for j in range(4)] for i in range(4)], dtype=np.float32)
        if not np.isfinite(pose).all() or not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6):
            raise ValueError("invalid frozen C2W pose")
        return torch.from_numpy(pose)

    def get_filepaths(self):
        colors: list[str] = []
        depths: list[str] = []
        self.tmp_poses: list[torch.Tensor] = []
        self.confidence_paths = []
        for row in self.records:
            colors.append(str(self._asset(row["rgb"])))
            depths.append(str(self._asset(row["depth"])))
            self.confidence_paths.append(self._asset(row["confidence"]))
            self._asset(row["intrinsics"])
            self.tmp_poses.append(self._pose(row))
        return colors, depths, None

    def load_poses(self):
        return self.tmp_poses

    def _record(self, index: int) -> dict[str, str]:
        return self.records[int(self.retained_inds[index].item())]

    def __getitem__(self, index: int):
        color, depth, _static_intrinsics, pose = super().__getitem__(index)
        row = self._record(index)
        intrinsics = torch.eye(4, device=depth.device, dtype=depth.dtype)
        intrinsics[0, 0] = float(row["fx"]) * self.width_downsample_ratio
        intrinsics[1, 1] = float(row["fy"]) * self.height_downsample_ratio
        intrinsics[0, 2] = float(row["cx"]) * self.width_downsample_ratio
        intrinsics[1, 2] = float(row["cy"]) * self.height_downsample_ratio
        source_index = int(self.retained_inds[index].item())
        confidence = np.asarray(imageio.imread(self.confidence_paths[source_index]))
        confidence = cv2.resize(confidence, (self.desired_width, self.desired_height), interpolation=cv2.INTER_NEAREST)
        mask = torch.from_numpy(confidence >= 1).to(device=depth.device)
        depth = depth.clone()
        depth[~mask.unsqueeze(-1)] = 0
        return color, depth, intrinsics, pose

    def canonical_frame_index(self, index: int) -> int:
        return int(self.retained_inds[index].item())

