"""Static checks for the minimal-diff source variants."""
from pathlib import Path
def test_variant_contracts() -> None:
    root=Path(__file__).parent / "source_variants" / "variants"
    e0=(root/"E0_EXACT_C3_BASELINE/tum_metric_depth_splatfacto.py").read_text()
    e1=(root/"E1_LATE_DEPTH_HOLD/tum_metric_depth_splatfacto.py").read_text(); e2=(root/"E2_REFINEMENT_LOCK_3000/tum_metric_depth_splatfacto.py").read_text(); e3=(root/"E3_LATE_DEPTH_HOLD_AND_LOCK/tum_metric_depth_splatfacto.py").read_text()
    assert "late_depth_hold" not in e0 and "refinement_lock_step" not in e0
    assert "late_depth_hold_lambda: float = 0.30" in e1 and "effective_lambda * depth_loss" in e1
    assert "refinement_lock_step: int | None = 3000" in e2 and "return super().step_post_backward(step)" in e2
    assert "late_depth_hold_lambda: float = 0.30" in e3 and "refinement_lock_step: int | None = 3000" in e3
    assert all(token not in e3 for token in ("instrumentation_path", "quantile", ".cpu()", "TumMetricGeometryRefinement"))
