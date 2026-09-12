"""Additive Stonehenge V3 query-space geometry wiring.

Importing this package performs no map loading, GPU work, rollout, or runtime
composition.  Callers must explicitly request the V3 policy and stack factory.
"""

from .geometry_policy import V3_GEOMETRY_POLICY, V3HardRadiusGeometryPolicy
from .stack_config import project_v3_runtime_config
from .stack_factory import build_v3_stack, build_v3_stack_from_frozen_v2, load_frozen_v2_build_stack

__all__ = [
    "V3_GEOMETRY_POLICY",
    "V3HardRadiusGeometryPolicy",
    "build_v3_stack",
    "build_v3_stack_from_frozen_v2",
    "load_frozen_v2_build_stack",
    "project_v3_runtime_config",
]
