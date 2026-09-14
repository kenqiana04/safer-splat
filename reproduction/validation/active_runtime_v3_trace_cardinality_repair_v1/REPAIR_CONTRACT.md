# Minimal repair contract

## Authorized change

1. Add a Supervisor-owned helper that represents an already-determined typed orchestration block as a no-commit `SupervisorDecision` with no selected action.
2. Pass every completed `_blocked_result` through the existing `ActiveRunner.commit_active_decision` boundary.
3. Reuse the existing `ActiveCommitTransaction` no-action branch to append exactly one trace outcome and perform zero plant commits and zero token mutations.

## Preserved authorities

- Routing interpretation remains `Supervisor.route_transition` and the frozen transition table.
- Final executable action selection remains `Supervisor.arbitrate`; the new block decision cannot select or commit an action.
- Plant authority remains `PlantCommitAdapter.commit` and is not called on the repaired path.
- Trace authority remains the existing `ActiveCommitTransaction` / `TraceWriter` chain.
- Backup-token mechanics remain unchanged.
- The post-L2 WARNING still prevents L3 discovery.

## Explicit non-changes

- No transition row, deadline threshold, stage budget, fallback priority, candidate policy, or terminal policy changes.
- No controller, CBF, certificate mathematics, dynamics, map, checkpoint, protocol, manifest, or analyzer changes.
- V3 runtime hard radius remains `0.015 q`; historical `0.025 q` receives no runtime authority.
- No old formal/pilot/smoke result is rewritten or reclassified.

## Acceptance

For the reproduced post-L2 block:

- completed public cycle delta: `+1`
- trace record delta: `+1`
- plant commit delta: `0`
- L3 evaluation delta: `0`
- selected and executed action: absent
- trace role: `ASSURANCE_BOUNDARY_NO_ACTION`
- transaction evidence: `NO_ACTION_COMPLETE`
- final trace lock count equals persisted line count and completed-cycle count
