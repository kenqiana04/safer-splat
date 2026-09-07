
# Backup cycle integration V2

The coordinator performs token mechanics only: read
`BackupTokenStore.current`, request the frozen validation against the exact
snapshot/authority registry, surface VALID/INVALID/NONE/EXHAUSTED/UNKNOWN,
and request invalidation only through the existing store API when the frozen
contract requires it. It may obtain the exact cursor action but never chooses
backup priority. Supervisor owns routing and arbitration.

On a navigation commit, reuse `ActiveRunner.commit_active_decision`: plant
commit, prepared bundle store, atomic activation of cursor k+1, old-token
retirement, then trace. On a backup commit, reuse the same path and advance
the cursor only after a successful plant receipt. The coordinator must not
duplicate either lifecycle.
