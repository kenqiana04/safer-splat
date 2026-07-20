"""Task-owned metric-depth Splatfacto subclass; no scale alignment is applied."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Type

import imageio.v3 as iio
import torch
import torch.nn.functional as F
from nerfstudio.models.splatfacto import SplatfactoModel, SplatfactoModelConfig


def metric_depth_huber_loss(prediction: torch.Tensor, target: torch.Tensor, accumulation: torch.Tensor, beta: float = 0.10) -> tuple[torch.Tensor, torch.Tensor]:
    """Metric Smooth-L1 over fixed valid pixels, preserving prediction gradients."""
    if target.shape != prediction.shape:
        target = F.interpolate(target[None, None], size=prediction.shape[-2:], mode="nearest")[0, 0]
    if accumulation.shape != prediction.shape:
        accumulation = F.interpolate(accumulation[None, None], size=prediction.shape[-2:], mode="nearest")[0, 0]
    valid = torch.isfinite(target) & torch.isfinite(prediction) & (target > 0) & (prediction > 0) & (accumulation > 1e-4)
    ratio = valid.float().mean()
    if not bool(valid.any()):
        return prediction.sum() * 0.0, ratio
    return F.smooth_l1_loss(prediction[valid], target[valid], beta=beta), ratio


@dataclass
class TumMetricDepthSplatfactoConfig(SplatfactoModelConfig):
    _target: Type = field(default_factory=lambda: TumMetricDepthSplatfactoModel)
    depth_loss_lambda: float = 0.10
    depth_loss_beta_m: float = 0.10
    depth_unit_scale_factor: float = 0.0002
    depth_accumulation_threshold: float = 1e-4
    output_depth_during_training: bool = True
    late_depth_hold_start: int | None = 3000
    late_depth_hold_lambda: float = 0.30
    refinement_lock_step: int | None = 3000


class TumMetricDepthSplatfactoModel(SplatfactoModel):
    config: TumMetricDepthSplatfactoConfig

    def _depth_target(self, image_index: int, device: torch.device) -> torch.Tensor:
        filenames = self.kwargs["metadata"]["depth_filenames"]
        depth = iio.imread(Path(filenames[image_index])).astype("float32") * self.config.depth_unit_scale_factor
        return torch.from_numpy(depth).to(device=device)

    def get_loss_dict(self, outputs, batch, metrics_dict=None) -> Dict[str, torch.Tensor]:
        loss_dict = super().get_loss_dict(outputs, batch, metrics_dict)
        index = int(batch["image_idx"].item()) if torch.is_tensor(batch["image_idx"]) else int(batch["image_idx"])
        prediction = outputs["depth"].squeeze(-1)
        accumulation = outputs["accumulation"].squeeze(-1)
        target = self._depth_target(index, prediction.device)
        depth_loss, valid_ratio = metric_depth_huber_loss(prediction, target, accumulation, self.config.depth_loss_beta_m)
        effective_lambda = self.config.depth_loss_lambda
        if self.config.late_depth_hold_start is not None and int(self.step) >= self.config.late_depth_hold_start:
            effective_lambda = self.config.late_depth_hold_lambda
        loss_dict["loss_depth_metric"] = effective_lambda * depth_loss
        loss_dict["valid_depth_ratio"] = valid_ratio
        if metrics_dict is not None:
            metrics_dict["loss_depth_metric"] = depth_loss.detach()
            metrics_dict["valid_depth_ratio"] = valid_ratio.detach()
        return loss_dict

    def step_post_backward(self, step: int):
        if self.config.refinement_lock_step is not None and step >= self.config.refinement_lock_step:
            return
        return super().step_post_backward(step)
