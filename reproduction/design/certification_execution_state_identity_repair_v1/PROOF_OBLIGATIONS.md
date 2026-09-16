# Proof Obligations

| ID | Obligation | Required evidence |
|---|---|---|
| PO1 | Plant bitwise equivalence | Archived and randomized state/action/dt fixtures show `T_exec` output equals the actual plant transition bitwise on the same execution backend. |
| PO2 | L1 action independence | All admissible representative actions yield the same immediate position bits; `T_pos_exec` matches them. |
| PO3 | L2 causal sensitivity | First-step velocity reflects `u_k`; first-step position does not. Second position reflects the causally prior action exactly as frozen dynamics require. |
| PO4 | Cross-cycle bitwise continuity | L2 `p_k1/p_k2`, realized `k+1/k+2`, and next L1 endpoint satisfy `CERTIFICATION_EXECUTION_CONTINUITY_INVARIANT_V1`. |
| PO5 | Certifier segment identity | L1/L2/L3/backup/terminal certifiers receive endpoints carrying the same canonical identities used by continuity checks. |
| PO6 | Backup-chain continuity | Prepared bundle states and retained token expectations follow sequential `T_exec`; cursor actions and realized snapshots match. |
| PO7 | No policy drift | Controller, candidate selection, Supervisor priority, deadlines, map, dynamics, dt, actuator bounds, and experiment/statistics remain unchanged. |
| PO8 | 0.025 no authority | Static and runtime evidence prove the historical 0.025 q shell never enters certification, routing, arbitration, fallback, or plant commit. |
| PO9 | Frozen failure preserved | `FAIL_V3_HARD_SAFETY_GATE`, the four Active violation trial IDs, and all paired outcomes remain immutable historical evidence. |
| PO10 | Trace completeness | Every resolved cycle records transition and state identities plus typed match status; no untraced commit or scientifically eligible incomplete record exists. |

All ten obligations are blocking. Passing these obligations establishes identity correctness only; it does not establish safety efficacy, noninferiority, real-time behavior, or deployment readiness.
