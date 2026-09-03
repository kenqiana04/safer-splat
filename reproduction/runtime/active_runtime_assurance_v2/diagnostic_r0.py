"""R0 observation with no hard-gate, selection, commit, or mutation authority."""

from .runtime_types import R0Diagnostic, RuntimeStateSnapshot


class DiagnosticR0:
    def inspect(self, snapshot: RuntimeStateSnapshot) -> R0Diagnostic:
        return R0Diagnostic(snapshot.identity, "R0_DIAGNOSTIC_COMPLETE")
