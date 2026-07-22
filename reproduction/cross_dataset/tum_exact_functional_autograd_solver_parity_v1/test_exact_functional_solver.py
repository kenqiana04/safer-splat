"""Synthetic source-forward and functional-autograd parity gate."""
from __future__ import annotations
import json
from pathlib import Path
import torch
from splat.distances import distance_point_ellipsoid
from exact_functional_ellipsoid_solver import exact_functional_distance_point_ellipsoid

torch.manual_seed(20260722)
device = torch.device("cuda:0")
scales = torch.rand(4096, 3, device=device, dtype=torch.float32).mul_(0.25).add_(0.001)
scales, _ = torch.sort(scales, dim=-1, descending=True)
points = torch.randn(4096, 3, device=device, dtype=torch.float32).mul_(0.7)
official_distance, official_grad, _, official_yhat = distance_point_ellipsoid(scales, points)
functional_distance, functional_yhat = exact_functional_distance_point_ellipsoid(scales, points)
query = points.detach().clone().requires_grad_(True)
functional_for_grad, _ = exact_functional_distance_point_ellipsoid(scales, query)
functional_grad = torch.autograd.grad(functional_for_grad.sum(), query)[0]
out = {"case_count": 4096, "forward_distance_torch_equal": bool(torch.equal(official_distance, functional_distance)), "forward_yhat_torch_equal": bool(torch.equal(official_yhat, functional_yhat)), "h_max_abs_diff": float((official_distance-functional_distance).abs().max()), "gradient_max_abs_diff": float((official_grad-functional_grad).abs().max()), "gradient_cosine_min": float(torch.nn.functional.cosine_similarity(official_grad, functional_grad, dim=-1).min()), "status": "PASS_SYNTHETIC_EXACT_FUNCTIONAL_PARITY" if torch.equal(official_distance, functional_distance) and torch.equal(official_yhat, functional_yhat) else "FAIL"}
Path(__file__).with_name("synthetic_parity_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
print(json.dumps(out, sort_keys=True))
