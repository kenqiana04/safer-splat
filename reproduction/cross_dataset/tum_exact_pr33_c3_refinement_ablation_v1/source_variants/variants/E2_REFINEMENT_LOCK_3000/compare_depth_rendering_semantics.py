"""Document native depth semantics before raw metric comparison.

Nerfstudio Splatfacto's available native output here is the expected depth from
the gsplat ``RGB+ED`` render path.  Accumulated/alpha-normalized/median/first
depth are not exposed as equivalent native outputs in this installed API, so
they are explicitly not substituted into the metric gate.
"""
NATIVE_SEMANTIC = "expected_depth_from_splatfacto_RGB+ED"
UNAVAILABLE_ALTERNATIVES = ("accumulated_depth", "alpha_normalized_depth", "native_median_depth", "native_first_depth")
