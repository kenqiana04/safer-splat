# REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1

The preregistered audit reached **Case C**. Replica 0/160 was reproduced, and two additional official learned-map environments each supplied 100 frozen, method-independent representative states, yet all three environments had zero segment, backup, or directional incremental events. This rules out ‘Replica is simply too easy’ as a sufficient explanation. It supports a bounded rare-event/configuration-dominance interpretation, not a universal non-activation or safety claim.

## Required final fields

1. **branch:** `core-v1-cross-environment-activation-portability-audit-v1`
2. **Draft PR:** created after validation; see final handoff
3. **commit:** created after validation
4. **base/head:** `research-direction-novelty-data-winnability-audit-v1` / task result commit; base SHA `9287617cce74561aa434d1aca7eb684f79551188`
5. **PR #84–#88 preserved:** yes; heads `{84: '04ebca2b1b35124ad0e61ebed96e491c9edae4bb', 85: '7afef38392bec36d9d9811e5a22c816da5faf1ff', 86: 'd4f20f44a810afc2d6379853a286a3e18b175221', 87: 'fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9', 88: '9287617cce74561aa434d1aca7eb684f79551188'}`; no amend/rebase/merge/close/force-push
6. **certifier identity:** PR #84 `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`; protected raw Git blobs frozen in `input_freeze/protected_source_hashes.json`
7. **library identity/SHA:** PR #86 `d4f20f44a810afc2d6379853a286a3e18b175221` / `3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe`
8. **frozen model/config:** `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`; dt=0.05; |u|∞≤0.1; |v|∞≤0.1; radius=0.1; margin=0.01; terminal tolerance=1e-12; H_stop,max=20
9. **preregistered environment count:** 7; no E8
10. **environment readiness:** formal E1/E5/E6; structural shortfall E2/E3/E4; diagnostic-only E7
11. **reference tiers:** E1 R3; E3/E4 observable R2 but structurally short; E5/E6 R1 behavior only; E2 not evaluable; E7 N0
12. **excluded/not-evaluable:** E2 lacks frozen route contract; E3/E4 have 1/238 bounds-valid trajectory states; E7 excluded diagnostic
13. **Replica registry identity:** `eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a` (exact PR #87 reuse)
14. **candidate pools:** `{'E1_REPLICA_GT_FINE': 160, 'E2_ETH3D_LEARNED_GAUSSIAN': 0, 'E3_TUM_SPLATAM': 1, 'E4_TUM_GAUSSIAN_SLAM': 1, 'E5_STONEHENGE_SAFER': 100, 'E6_FLIGHT_SAFER': 100, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 0}`
15. **registry count/SHA:** counts `{'E1_REPLICA_GT_FINE': 160, 'E2_ETH3D_LEARNED_GAUSSIAN': 0, 'E3_TUM_SPLATAM': 0, 'E4_TUM_GAUSSIAN_SLAM': 0, 'E5_STONEHENGE_SAFER': 100, 'E6_FLIGHT_SAFER': 100, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 0}`; SHAs `{'E1_REPLICA_GT_FINE': 'eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a', 'E2_ETH3D_LEARNED_GAUSSIAN': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'E3_TUM_SPLATAM': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'E4_TUM_GAUSSIAN_SLAM': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'E5_STONEHENGE_SAFER': '5827534b7fe7a8296a11227dc5516f538d4841f4166a7cac4a40577e58dc3242', 'E6_FLIGHT_SAFER': 'bf07fdca87c588fdebfe6e005e3fba0a0ed68a11799b3ca38079588f0aed107d', 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570'}`
16. **registry rebuild:** three fresh processes per environment; all SHA triplets identical
17. **prelock method runs:** 0
18. **prelock future-reference reads:** 0
19. **selection leakage:** none; official trial outcome columns were not consumed; post-lock replacement=0
20. **formal attempt:** 1; infrastructure failure=0; same-manifest resume=0
21. **one-step states/method records:** 360 / 1440
22. **Replica reproduction:** segment=0/160, backup=0/160, directional=0/160, B3 fail-closed=0/160
23. **segment incremental by environment:** `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 0, 'E6_FLIGHT_SAFER': 0, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
24. **backup incremental by environment:** `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 0, 'E6_FLIGHT_SAFER': 0, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
25. **directional rescue by environment:** `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 0, 'E6_FLIGHT_SAFER': 0, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
26. **any incremental by environment:** `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 0, 'E6_FLIGHT_SAFER': 0, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
27. **Wilson 95% CIs for any activation:** `{'E1_REPLICA_GT_FINE': (0.0, 0.02344619517150519), 'E5_STONEHENGE_SAFER': (0.0, 0.03699349820698568), 'E6_FLIGHT_SAFER': (0.0, 0.03699349820698568)}`; excluded environments are NOT_EVALUATED
28. **natural rollout episodes:** 0 because natural incremental event count=0; no artificial activated replacement
29. **rollout progress:** NOT_EVALUABLE; logical rollout steps=0
30. **current infeasible:** E1=0, E5=100, E6=74 at B3; exact B0 counts in per-environment summary
31. **terminal-already-safe:** E1=35; E5=0; E6=26; never counted as backup incremental
32. **fail-closed:** B3 state count `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 100, 'E6_FLIGHT_SAFER': 74, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
33. **UNKNOWN/nonfinite:** `{'E1_REPLICA_GT_FINE': 0, 'E2_ETH3D_LEARNED_GAUSSIAN': 'NOT_EVALUATED', 'E3_TUM_SPLATAM': 'NOT_EVALUATED', 'E4_TUM_GAUSSIAN_SLAM': 'NOT_EVALUATED', 'E5_STONEHENGE_SAFER': 0, 'E6_FLIGHT_SAFER': 0, 'E7_TUM_SPLATFACTO_NEGATIVE_CONTROL': 'NOT_EVALUATED'}`
34. **clearance/exposure:** post-lock descriptors are in `environment_features/`; physical clearance exists only for E1; represented proxy is not substituted for reference clearance
35. **activation–exposure association:** not estimable because evaluated activation is identically zero
36. **map-reference disagreement:** E1=0; E5/E6 and shortfall environments NOT_EVALUABLE
37. **represented false-safe:** 0
38. **offline reference collision:** 0 for E1; E5/E6 NOT_EVALUABLE
39. **reference-safe-but-rejected:** E1=0; behavior-only tiers NOT_EVALUABLE
40. **runtime by environment/method:** see `benchmark/runtime_summary.csv`; behavior-only environments are far over 50 ms
41. **50 ms deadline misses:** 933 / 1440 method records
42. **H1–H7:** H1 pass; H2 no variation; H3 fail; H4 pass; H5/H6 not estimable; H7 limitation retained; Holm family did not create a positive claim
43. **environment-qualified signals:** 0
44. **portability P1–P10:** `{'P1': False, 'P2': False, 'P3': False, 'P4': False, 'P5': True, 'P6': True, 'P7': True, 'P8': True, 'P9': True, 'P10': True}`; overall fail
45. **competing explanations:** A not supported; B configuration dominance supported descriptively; C rare-event character supported descriptively; D map-error artifact not used
46. **cross-environment Case A–E:** `CASE_C`
47. **supported claims:** frozen mechanism-control evidence remains; representative incremental activation was 0 in all three evaluated environments; the current configuration is compatible with a rare-event supervisor interpretation
48. **prohibited claims:** collision superiority, universal safety/non-activation, deployment readiness, realtime, cross-map certificate, broad SAFER replacement
49. **unresolved evidence:** independent geometry for E5/E6; an eligible learned-map R2/R3 cohort; delay/disturbance/tracking robustness; runtime optimization
50. **training/mutation:** map training=0; map mutation=0; dataset/map/checkpoint creation=0
51. **controller/method/parameter changes:** 0 / 0 / 0
52. **protected-source mutation:** 0
53. **GPU/process final:** verified clean after formal execution in final system audit
54. **watchdog/SSH:** system watchdog and unrelated SSH preserved; no network service/firewall/route action
55. **operational autonomy:** three task-level observation/reporting/type-bridge actions, all non-semantic and recorded
56. **validator:** `PASS_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_AUDIT_VALIDATION`
57. **FINAL_STATUS:** `NO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL`
58. **FINAL_DECISION:** `UPHOLD_PR88_CASE_D_AND_STOP_CORE_V1_METHOD_EXPANSION`
59. **server/local report:** authoritative task root plus this Git report; only this REPORT is copied to Desktop/REPORT
60. **downstream handoff:** preserve PR #88 Case D; consolidate bounded evidence; do not resume method expansion
61. **Only next task:** `WRITE_FROZEN_PAPER_CONTRIBUTION_AND_EXPERIMENT_PLAN_V1`

## Historical facts preserved

The frozen Replica ACTIVATED cohort remains a mechanism control only: G1 segment discrimination 20/20, G2/G3 terminal/backup changes 40/40, G3 directional rescue 20/20 with positive short-rollout progress, and represented false-safe 0. The frozen Replica representative result remains segment 0/160, backup 0/160, directional 0/160, B3 fail-closed 0/160, reference collision 0, and historical B3 50 ms deadline misses 116/260. The current audit does not erase either evidence set; it limits prevalence and external-validity claims.

## Decision

`FINAL_STATUS=NO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL`

`FINAL_DECISION=UPHOLD_PR88_CASE_D_AND_STOP_CORE_V1_METHOD_EXPANSION`

Only next task: `WRITE_FROZEN_PAPER_CONTRIBUTION_AND_EXPERIMENT_PLAN_V1`
