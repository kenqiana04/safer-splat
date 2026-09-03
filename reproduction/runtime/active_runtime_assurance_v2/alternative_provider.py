"""Lawful native-existing alternatives only; the frozen inventory is empty."""

from __future__ import annotations

from typing import Callable, Iterable

from .runtime_types import AlternativeInventoryResult, Candidate, RuntimeStateSnapshot


class NativeExistingAlternativeProvider:
    def __init__(self, supplier: Callable[[RuntimeStateSnapshot], Iterable[Candidate]] | None = None) -> None:
        self._supplier = supplier

    def enumerate(self, snapshot: RuntimeStateSnapshot) -> AlternativeInventoryResult:
        candidates = () if self._supplier is None else tuple(self._supplier(snapshot))
        for candidate in candidates:
            if candidate.provenance.source_type != "SOURCE_NATIVE_EXISTING" or not candidate.provenance.lawful:
                return AlternativeInventoryResult("SOURCE_INVALID", ())
            if candidate.provenance.state_identity != snapshot.identity or candidate.provenance.map_identity != snapshot.map_identity:
                return AlternativeInventoryResult("PROVENANCE_MISSING", ())
        return AlternativeInventoryResult("ALT_AVAILABLE" if candidates else "NO_ALTERNATIVE_AVAILABLE", candidates)
