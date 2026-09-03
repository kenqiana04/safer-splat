# Plant Commit Boundary V2

The sole state-changing chain is:

`SupervisorDecision -> SelectedAction -> exact identity check -> PlantCommitAdapter.commit -> CommitReceipt -> token/event update -> trace append`.

Only `Supervisor.arbitrate` may select an action. Only `PlantCommitAdapter.commit` may invoke the frozen position-first forward-Euler double-integrator transition. Certification layers, proposal adapters, alternative providers, token stores, terminal membership checks, deadlines, trace writers, and the post-hoc oracle have no plant authority.

`SelectedAction` contains an explicit role (`PRIMARY_NAVIGATION`, `ALTERNATIVE_NAVIGATION`, `RETAINED_BACKUP`, `CERTIFIED_TERMINAL`, or `ASSURANCE_BOUNDARY_NO_ACTION`), action ID, exact vector hash, state ID, cycle ID, authority bundle, certificate references, and optional prepared-token ID. Role is never inferred from vector value. A zero vector may remain primary navigation; terminal status exists only when the Supervisor selected the canonical terminal identity under the terminal contract.

Before the plant call, `PlantCommitAdapter` requires exact selected/executed identity, current state/time/map/geometry/actuator authority matches, and a commit-bearing Supervisor decision. Failure produces a typed `CommitReceipt` with no dynamics call. A successful navigation receipt atomically activates its prepared token for k+1. A successful backup receipt advances the existing token cursor exactly once. Failed commits do neither. The assurance boundary always returns a no-action receipt and performs no plant step.
