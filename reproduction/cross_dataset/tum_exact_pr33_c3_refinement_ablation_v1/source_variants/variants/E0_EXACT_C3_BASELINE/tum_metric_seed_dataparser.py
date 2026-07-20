"""Train-only metric RGB-D seed injection for the frozen TUM dataparser."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

import numpy as np
import torch
from nerfstudio.configs.base_config import InstantiateConfig
from nerfstudio.data.dataparsers.base_dataparser import DataParser, DataParserConfig, DataparserOutputs


@dataclass
class TumMetricSeedDataParserConfig(DataParserConfig):
    """Wrap an existing parser without changing its cameras, images, or split."""

    _target: Type = field(default_factory=lambda: TumMetricSeedDataParser)
    base_dataparser: DataParserConfig = field(default_factory=DataParserConfig)
    seed_points_npz: Path = Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz")


class TumMetricSeedDataParser(DataParser):
    config: TumMetricSeedDataParserConfig

    def __init__(self, config: TumMetricSeedDataParserConfig):
        super().__init__(config=config)
        self._base = config.base_dataparser.setup()

    def _generate_dataparser_outputs(self, split: str = "train") -> DataparserOutputs:
        output = self._base.get_dataparser_outputs(split=split)
        metadata = dict(output.metadata)
        if split == "train":
            seed = np.load(self.config.seed_points_npz)
            metadata["points3D_xyz"] = torch.from_numpy(seed["xyz"].astype(np.float32, copy=False))
            metadata["points3D_rgb"] = torch.from_numpy(seed["rgb"].astype(np.float32, copy=False))
            metadata["tum_metric_seed_source"] = "train_only_rgbd_voxel_0.02m"
        output.metadata = metadata
        return output
