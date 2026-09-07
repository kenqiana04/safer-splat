
# Primary cycle integration V2

After CYCLE_BEGIN and one authoritative L1 evaluation, a Supervisor routing
decision may admit `PrimaryProposalAdapter`. A proposal is a typed
PRIMARY_AVAILABLE/UNAVAILABLE/UNKNOWN result and has no commit authority.
When a candidate identity exists, the coordinator creates a fresh
`L1AttemptBinding` for that candidate and executes the frozen order C0 -> L2
-> L3. `Supervisor.certify_candidate` can be reused for the existing C0/L2/L3
certificate path but does not replace the public composition root.

Only Supervisor arbitration may select the primary action. A primary C0/L2/L3
failure is an event, not an implicit backup or nominal-control instruction.
