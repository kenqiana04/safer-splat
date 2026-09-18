# Trial-local exhaustion

The key hashes canonical numeric state bits, goal, dt, map, source/generator, actuator, geometry, transition, backend and backup-routing class. Trial/cycle index is excluded from the key, but each record is scoped to the active trial. A finite cursor and tried-control set prevent reattempt of the same canonical vector. `PAUSED` can resume at the next untried rank; `EXHAUSTED`, `SELECTED` and `BLOCKED` cannot restart. Finalization clears the register for a later trial. The source emits at most six controls; there is no unbounded internal search.
