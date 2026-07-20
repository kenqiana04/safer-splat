"""Task-owned C3 instrumentation, fixed depth schedules, and refinement lock."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Type

import torch

from tum_metric_depth_splatfacto import TumMetricDepthSplatfactoConfig, TumMetricDepthSplatfactoModel

Schedule = Literal["CONSTANT_010", "LATE_HOLD_030"]
RefinementMode = Literal["STOCK_REFINEMENT", "LOCK_AFTER_3000"]


def scheduled_depth_lambda(schedule: Schedule, step: int) -> float:
    if schedule == "CONSTANT_010":
        return 0.10
    if schedule == "LATE_HOLD_030":
        return 0.10 if step < 3000 else 0.30
    raise ValueError(f"unknown schedule: {schedule}")


@dataclass
class TumMetricGeometryRefinementConfig(TumMetricDepthSplatfactoConfig):
    _target: Type = field(default_factory=lambda: TumMetricGeometryRefinementModel)
    depth_schedule: Schedule = "CONSTANT_010"
    refinement_mode: RefinementMode = "STOCK_REFINEMENT"
    refinement_lock_step: int = 3000
    instrumentation_path: str = ""


class TumMetricGeometryRefinementModel(TumMetricDepthSplatfactoModel):
    config: TumMetricGeometryRefinementConfig

    def get_loss_dict(self, outputs, batch, metrics_dict=None):
        losses = super().get_loss_dict(outputs, batch, metrics_dict)
        current_lambda = scheduled_depth_lambda(self.config.depth_schedule, int(self.step))
        # Parent computes a fixed 0.10-weighted depth term.  Rescale only that
        # differentiable term; the metric-depth formula, beta and mask remain fixed.
        if current_lambda != 0.10:
            losses["loss_depth_metric"] = losses["loss_depth_metric"] * (current_lambda / 0.10)
        self._last_losses = {
            "current_depth_lambda": current_lambda,
            "total_loss": float(sum(v.detach() for k, v in losses.items() if "loss" in k).cpu()),
            "rgb_loss": float(losses.get("main_loss", torch.zeros((), device=self.device)).detach().cpu()),
            "depth_loss": float(losses["loss_depth_metric"].detach().cpu()),
            "valid_depth_ratio": float(losses.get("valid_depth_ratio", torch.zeros((), device=self.device)).detach().cpu()),
        }
        return losses

    def _record_event(self, step: int, before: int, after: int, lock_active: bool) -> None:
        if not self.config.instrumentation_path or step % 100:
            return
        with torch.no_grad():
            scale = torch.exp(self.scales.detach()).flatten()
            opacity = torch.sigmoid(self.opacities.detach()).flatten()
            gradients = [p.grad.detach().norm() for p in self.gauss_params.values() if p.grad is not None]
            row = {
                "step": int(step), "wall_time": time.time(), **getattr(self, "_last_losses", {}),
                "gaussian_count": int(after), "means_finite": bool(torch.isfinite(self.means).all()),
                "scales_finite": bool(torch.isfinite(self.scales).all()), "opacity_finite": bool(torch.isfinite(self.opacities).all()),
                "mean_scale": float(scale.mean()), "median_scale": float(scale.median()),
                "p95_scale": float(torch.quantile(scale, .95)), "p99_scale": float(torch.quantile(scale, .99)),
                "mean_opacity": float(opacity.mean()), "median_opacity": float(opacity.median()), "p95_opacity": float(torch.quantile(opacity, .95)),
                "gradient_norm": float(torch.stack(gradients).norm()) if gradients else 0.0,
                "cuda_allocated_memory": int(torch.cuda.memory_allocated()), "cuda_reserved_memory": int(torch.cuda.memory_reserved()),
                "split_count": None, "duplicate_count": None, "cull_count": None,
                "opacity_reset_event": bool(step > 0 and step % (self.config.reset_alpha_every * self.config.refine_every) == 0 and not lock_active),
                "refinement_event_type": "LOCKED" if lock_active else ("STOCK_STRATEGY" if step > self.config.warmup_length and step % self.config.refine_every == 0 else "NONE"),
                "gaussian_count_before_event": int(before), "gaussian_count_after_event": int(after),
                "net_gaussian_count_change": int(after - before), "refinement_lock_active": lock_active,
            }
        path = Path(self.config.instrumentation_path); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def step_post_backward(self, step: int):
        assert step == self.step
        before = int(self.num_points)
        locked = self.config.refinement_mode == "LOCK_AFTER_3000" and step >= self.config.refinement_lock_step
        if not locked:
            super().step_post_backward(step)
        self._record_event(step, before, int(self.num_points), locked)
