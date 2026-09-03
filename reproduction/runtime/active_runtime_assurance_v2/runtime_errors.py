"""Typed runtime failures; none authorize a fallback action."""


class ActiveRuntimeError(RuntimeError):
    """Base class for typed implementation/runtime failures."""


class StartupConfigurationError(ActiveRuntimeError):
    """Required frozen authority or configuration is absent."""


class AuthorityMismatch(StartupConfigurationError):
    """An authority identity or value differs from the frozen contract."""


class DeadlineProfileRequired(StartupConfigurationError):
    """ACTIVE mode has no explicit RuntimeDeadlineProfile."""


class CommitAuthorityViolation(ActiveRuntimeError):
    """A caller tried to commit without a legal Supervisor decision."""


class TraceFinalizedError(ActiveRuntimeError):
    """Append attempted after the immutable trace lock was created."""


class TokenLifecycleViolation(ActiveRuntimeError):
    """Backup token mutation violates the PR #112 lifecycle."""
