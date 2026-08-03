"""Task-owned empty-depth compatibility primitives for the frozen M1 contract.

The nonempty branches deliberately delegate to the caller's official SplaTAM
functions.  The only new behavior is defined for an empty depth-valid mask.
"""

from __future__ import annotations

from typing import Any, Callable

import torch


EMPTY_EVENT = "EMPTY_DEPTH_SAFE_SKIP_DEPTH_INITIALIZATION"
NONEMPTY_EVENT = "OFFICIAL_NONEMPTY_DEPTH_PATH"


def safe_masked_mean(values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Return the official masked mean, or a differentiable exact zero if empty."""
    if values.device != mask.device:
        raise ValueError("values and mask must share a device")
    if mask.dtype is not torch.bool:
        mask = mask.to(dtype=torch.bool)
    if mask.shape != values.shape:
        try:
            mask = torch.broadcast_to(mask, values.shape)
        except RuntimeError as exc:
            raise ValueError("mask is not broadcastable to values") from exc
    selected = values[mask]
    if selected.numel() > 0:
        return selected.mean()
    return values.sum() * 0.0


def compute_mapping_losses_empty_depth_safe(
    predicted_depth: torch.Tensor,
    target_depth: torch.Tensor,
    predicted_rgb: torch.Tensor,
    target_rgb: torch.Tensor,
    rgb_loss_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    loss_weights: dict[str, float],
    *,
    valid_mask: torch.Tensor | None = None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor], dict[str, Any]]:
    """Compose official-equivalent nonempty mapping losses with an empty-safe depth term."""
    if predicted_depth.shape != target_depth.shape:
        raise ValueError("predicted and target depth shapes differ")
    if predicted_rgb.shape != target_rgb.shape:
        raise ValueError("predicted and target RGB shapes differ")
    if valid_mask is None:
        valid_mask = target_depth > 0
    valid_mask = valid_mask.to(device=predicted_depth.device, dtype=torch.bool)
    valid_mask = valid_mask & torch.isfinite(predicted_depth) & torch.isfinite(target_depth)
    depth_error = torch.abs(target_depth - predicted_depth)
    depth_loss = safe_masked_mean(depth_error, valid_mask)
    image_loss = rgb_loss_fn(predicted_rgb, target_rgb)
    weighted = {
        "depth": depth_loss * float(loss_weights["depth"]),
        "im": image_loss * float(loss_weights["im"]),
    }
    total = weighted["depth"] + weighted["im"]
    components = {"depth": depth_loss, "im": image_loss, "loss": total}
    metadata = {
        "valid_depth_count": int(valid_mask.sum().item()),
        "empty_depth_safe": not bool(valid_mask.any().item()),
        "depth_event": EMPTY_EVENT if not bool(valid_mask.any().item()) else NONEMPTY_EVENT,
    }
    return total, components, metadata


def maybe_initialize_depth_points_empty_depth_safe(
    valid_depth_mask: torch.Tensor,
    official_get_pointcloud: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, dict[str, Any]]:
    """Delegate nonempty point initialization; return typed empty outputs otherwise."""
    flat_mask = valid_depth_mask.reshape(-1).to(dtype=torch.bool)
    count = int(flat_mask.sum().item())
    if count > 0:
        result = official_get_pointcloud(*args, mask=flat_mask, **kwargs)
        return result, {"event": NONEMPTY_EVENT, "valid_depth_count": count, "added_count": count}
    color = args[0]
    dtype = color.dtype
    device = color.device
    empty_points = torch.empty((0, 6), dtype=dtype, device=device)
    if bool(kwargs.get("compute_mean_sq_dist", False)):
        result = (empty_points, torch.empty((0,), dtype=dtype, device=device))
    else:
        result = empty_points
    return result, {"event": EMPTY_EVENT, "valid_depth_count": 0, "added_count": 0}


def maybe_add_new_gaussians_empty_depth_safe(
    valid_depth_mask: torch.Tensor,
    params: Any,
    variables: Any,
    official_add_fn: Callable[..., tuple[Any, Any]],
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, Any, dict[str, Any]]:
    """Delegate official addition for nonempty depth; preserve state objects if empty."""
    count = int(valid_depth_mask.to(dtype=torch.bool).sum().item())
    if count == 0:
        return params, variables, {"event": EMPTY_EVENT, "valid_depth_count": 0, "added_count": 0}
    before = int(params["means3D"].shape[0]) if isinstance(params, dict) and "means3D" in params else None
    new_params, new_variables = official_add_fn(params, variables, *args, **kwargs)
    after = int(new_params["means3D"].shape[0]) if isinstance(new_params, dict) and "means3D" in new_params else None
    added = after - before if before is not None and after is not None else None
    return new_params, new_variables, {"event": NONEMPTY_EVENT, "valid_depth_count": count, "added_count": added}
