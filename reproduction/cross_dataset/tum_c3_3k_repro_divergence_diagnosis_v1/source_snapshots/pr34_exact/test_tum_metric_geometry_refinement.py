import torch

from tum_metric_geometry_refinement_model import scheduled_depth_lambda


def test_schedule_contract_and_gradients() -> None:
    assert scheduled_depth_lambda("CONSTANT_010", 0) == scheduled_depth_lambda("CONSTANT_010", 9999) == 0.10
    assert scheduled_depth_lambda("LATE_HOLD_030", 0) == scheduled_depth_lambda("LATE_HOLD_030", 2999) == 0.10
    assert scheduled_depth_lambda("LATE_HOLD_030", 3000) == scheduled_depth_lambda("LATE_HOLD_030", 9999) == 0.30
    value = (torch.tensor(2.0, requires_grad=True) * scheduled_depth_lambda("LATE_HOLD_030", 3000)) ** 2
    value.backward(); assert torch.isfinite(value) and torch.isfinite(torch.tensor(2.0))
