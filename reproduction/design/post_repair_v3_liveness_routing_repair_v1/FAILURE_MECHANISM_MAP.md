# Competing liveness mechanisms

| ID | Mechanism | Static evidence | Frozen trace support | Counterevidence / gap | Confidence |
|---|---|---|---|---|---|
| M1 | Terminal state-machine lock | None; `active_cycle.py:392-563` starts L1/P0 each cycle | Terminal streaks exist | No terminal-mode bypass; new cycle can re-enter primary | NOT_SUPPORTED |
| M2 | Dynamic fixed-point lock | `terminal_runtime.py`, `supervisor.py:443`, zero acceleration; frozen dynamics | Bottom ten terminal steps have exact numeric pre/post equality; several 500/500 terminal | This is a local fixed point, not proof why L3 fails | SUPPORTED |
| M3 | L3 certifiability bottleneck | `repaired_components.py:189-244` and BackupCertifier full finite witness | 27,367/42,500 L3 FAIL; bottom ten terminal-dominant | Per-attempt L3 reason not logged; cannot identify which subcertificate dominates | PARTIALLY_SUPPORTED |
| M4 | Backup coverage gap | `backup_token_store.py:42-59`; L3 fail with no valid token routes fallback | 602 retained-backup commits vs 26,770 terminal; bottom-tail examples lack backup | Counts do not prove why token unavailable; no per-attempt token-reason trace | PARTIALLY_SUPPORTED |
| M5 | Deadline routing effect | Supervisor forbids new search after guard | Only five WARNING, zero EXPIRED observations | Cannot account for widespread terminal cycles | NOT_SUPPORTED |
| M6 | Terminal re-entry gap | Existing native provider has empty inventory; no separate recovery source | Terminal-only numerical fixed points persist | Normal primary is re-evaluated each cycle; "re-entry gap" means candidate-source/certifiability gap, not state-machine prohibition | PARTIALLY_SUPPORTED |
| M7 | Mixed mechanism | M2 + M3 + M4 + M6 can coexist | Strong descriptive routing correlations | No randomized or interventional identification | PARTIALLY_SUPPORTED |

Primary design hypothesis: **M2 dynamic numeric-state fixed point coupled to M3 L3 certifiability and M4/M6 absence of a different fully certified local candidate**. This is not a claim that identity repair caused the fixed point or that terminal is unsafe. An implementation needs additive typed L3 failure-reason logging before it can refine M3.
