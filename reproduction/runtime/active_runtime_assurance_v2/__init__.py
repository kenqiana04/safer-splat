"""Additive Active Runtime Assurance V2.

Importing this package performs no rollout, GPU work, map loading, or outcome
evaluation. Runtime composition is explicit through :mod:`active_runner`.
"""

from .runtime_types import ActionRole, CertificateStatus, RuntimeMode

__all__ = ["ActionRole", "CertificateStatus", "RuntimeMode"]
