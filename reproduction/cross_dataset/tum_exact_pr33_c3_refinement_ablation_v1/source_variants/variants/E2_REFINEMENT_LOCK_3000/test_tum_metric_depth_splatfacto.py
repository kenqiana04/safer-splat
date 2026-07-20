from __future__ import annotations

import torch
from tum_metric_depth_splatfacto import metric_depth_huber_loss


def test_metric_depth_loss_contract() -> None:
    target = torch.ones((4, 4))
    accumulation = torch.ones((4, 4))
    perfect = torch.ones((4, 4), requires_grad=True)
    scaled = torch.full((4, 4), 0.2, requires_grad=True)
    zero_loss, ratio = metric_depth_huber_loss(perfect, target, accumulation)
    bad_loss, _ = metric_depth_huber_loss(scaled, target, accumulation)
    assert float(zero_loss) < 1e-7 and float(ratio) == 1.0
    assert float(bad_loss) > float(zero_loss)
    bad_loss.backward()
    assert torch.isfinite(scaled.grad).all()
    invalid = torch.zeros((4, 4))
    masked_loss, masked_ratio = metric_depth_huber_loss(scaled.detach(), invalid, accumulation)
    assert float(masked_loss) == 0.0 and float(masked_ratio) == 0.0
