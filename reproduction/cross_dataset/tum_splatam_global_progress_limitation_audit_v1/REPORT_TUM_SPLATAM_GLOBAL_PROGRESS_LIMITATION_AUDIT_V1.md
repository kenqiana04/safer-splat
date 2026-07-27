# TUM SplaTAM Global Progress-Limitation Offline Audit V1

**Status:** `PASS_TUM_GLOBAL_PROGRESS_LIMITATION_OFFLINE_AUDIT`.

## Scope and evidence

- Offline-only audit of saved terminal trajectories from PR #47, PR #48 shadow provenance, PR #49, and paused paired20. No rollout, sequence 3, QP execution, V4-C execution, Start-Safe, Risk-Aware, or tuning occurred.
- Canonical closed-loop trajectories: 10; complete paired comparisons: 5; incomplete logs: 0.
- Paused manifest SHA-256 remains `380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6` with state counts {'TERMINAL_SCIENTIFIC_RESULT': 2, 'NOT_STARTED': 38}.

## Progress semantics and trajectory outcomes

- `pr47_g1_baseline:0:50:ORIGINAL_SAFER_BASELINE`: terminal `TUM_SPLATAM_G1_COLLISION_STOP`; final/best geometric progress `0.6442220550023762`/`0.6442220550023762`; minimum distance `0.6594204642750352`; path length/efficiency `1.2749866176793503`/`0.9803801263269802`; last100 distance slope `-6.988944239551113e-06`; stall onset `None`; primary `EARLY_SAFETY_PROXY_STOP`; secondary `[]`.
- `pr49_v4c:0:50:STRICT_DT_TRIGGERED_V4C`: terminal `max_steps`; final/best geometric progress `0.6445665061961436`/`0.6445665061961436`; minimum distance `0.6587820395970868`; path length/efficiency `1.276494426933878`/`0.9791729818853612`; last100 distance slope `-8.818937217094889e-06`; stall onset `484`; primary `CBF_BOUNDARY_STALL`; secondary `['BASELINE_LIMITATION_PRESERVED']`.
- `pr49_v4c:1:51:ORIGINAL_SAFER_BASELINE`: terminal `gsplat_overlap_stop`; final/best geometric progress `0.6301709880396156`/`0.6301709880396156`; minimum distance `0.7134086902465441`; path length/efficiency `1.3058854697309243`/`0.9601354353331684`; last100 distance slope `-5.08330648393152e-06`; stall onset `519`; primary `EARLY_SAFETY_PROXY_STOP`; secondary `[]`.
- `pr49_v4c:1:51:STRICT_DT_TRIGGERED_V4C`: terminal `max_steps`; final/best geometric progress `0.6301688929706754`/`0.6301708711874903`; minimum distance `0.7134089156569876`; path length/efficiency `1.3070378946949133`/`0.9592852477758261`; last100 distance slope `-1.7363893782601982e-06`; stall onset `519`; primary `CBF_BOUNDARY_STALL`; secondary `['BASELINE_LIMITATION_PRESERVED']`.
- `pr49_v4c:8:58:ORIGINAL_SAFER_BASELINE`: terminal `max_steps`; final/best geometric progress `0.050863155356499705`/`0.050863155356499705`; minimum distance `2.289884934538851`; path length/efficiency `0.13213470462399074`/`0.9710873376039382`; last100 distance slope `9.485170044437083e-18`; stall onset `109`; primary `CBF_BOUNDARY_STALL`; secondary `['TRIGGER_NEUTRAL_BASELINE_EQUIVALENT']`.
- `pr49_v4c:8:58:STRICT_DT_TRIGGERED_V4C`: terminal `max_steps`; final/best geometric progress `0.050863155356499705`/`0.050863155356499705`; minimum distance `2.289884934538851`; path length/efficiency `0.13213470462399074`/`0.9710873376039382`; last100 distance slope `9.485170044437083e-18`; stall onset `109`; primary `CBF_BOUNDARY_STALL`; secondary `['TRIGGER_NEUTRAL_BASELINE_EQUIVALENT']`.
- `pr49_v4c:9:59:ORIGINAL_SAFER_BASELINE`: terminal `gsplat_overlap_stop`; final/best geometric progress `0.12213768153823211`/`0.12213768153823211`; minimum distance `2.1519727931104464`; path length/efficiency `0.32933854131593265`/`0.9124255696189542`; last100 distance slope `-1.9778633962189584e-06`; stall onset `435`; primary `EARLY_SAFETY_PROXY_STOP`; secondary `[]`.
- `pr49_v4c:9:59:STRICT_DT_TRIGGERED_V4C`: terminal `max_steps`; final/best geometric progress `0.12213825821693332`/`0.12213825821693332`; minimum distance `2.1519713794526902`; path length/efficiency `0.3312149821746032`/`0.9072605359558551`; last100 distance slope `-4.1213637238100036e-08`; stall onset `435`; primary `CBF_BOUNDARY_STALL`; secondary `['BASELINE_LIMITATION_PRESERVED']`.
- `paused_paired20:111:287:ORIGINAL_SAFER_BASELINE`: terminal `float32_proxy_overlap_stop`; final/best geometric progress `0.5391114396213177`/`0.5391114396213177`; minimum distance `0.25908149629012506`; path length/efficiency `0.3516951517561213`/`0.8976196652340119`; last100 distance slope `-1.2196196720926162e-06`; stall onset `194`; primary `EARLY_SAFETY_PROXY_STOP`; secondary `[]`.
- `paused_paired20:111:287:STRICT_DT_TRIGGERED_V4C`: terminal `max_steps`; final/best geometric progress `0.53908992060009`/`0.5391113336109417`; minimum distance `0.259081555882246`; path length/efficiency `0.35342338482804003`/`0.8932141128636956`; last100 distance slope `4.4320750034796044e-07`; stall onset `194`; primary `CBF_BOUNDARY_STALL`; secondary `['BASELINE_LIMITATION_PRESERVED']`.

## Attribution and paired findings

- GLOBAL_PRIMARY_CAUSE: `CBF_BOUNDARY_STALL`; secondary causes: `['EARLY_SAFETY_PROXY_STOP']`.
- Triggered-pair conclusions: [('0->50', 'AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION'), ('1->51', 'AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION'), ('111->287', 'AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION'), ('9->59', 'AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION')]
- Untriggered invariance: [('8->58', True)].
- Float32 proxy-stop avoidance is not reported as certified robust-overlap avoidance unless independent saved float64 certification explicitly supports it.
- Safety-mechanism behavior, navigation completion, and progress limitation remain separate claims.

## Paired20 decision and scheduler-race boundary

- Resume decision: `DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY`. No paired20 continuation was started.
- Scheduler-race fact preserved: sequence 3 briefly entered but wrote no terminal summary or step file; it is not a scientific result and resume point remains sequence 3.

## Claim boundary

This preliminary audit explains saved evidence only; it does not prove global goal reachability or general safety. Any controller study or paired20 continuation needs separate authorization.


## Offline metric interpretation

- Official-versus-geometric progress records: [('pr47_g1_baseline:0:50:ORIGINAL_SAFER_BASELINE', True, -3.7639152203894355e-06), ('pr49_v4c:0:50:STRICT_DT_TRIGGERED_V4C', True, 1.5868036262745022e-07), ('pr49_v4c:1:51:ORIGINAL_SAFER_BASELINE', True, 7.802972223913685e-08), ('pr49_v4c:1:51:STRICT_DT_TRIGGERED_V4C', True, 1.955705503098315e-07), ('pr49_v4c:8:58:ORIGINAL_SAFER_BASELINE', True, 2.8427618432858015e-08), ('pr49_v4c:8:58:STRICT_DT_TRIGGERED_V4C', True, 2.8427618432858015e-08), ('pr49_v4c:9:59:ORIGINAL_SAFER_BASELINE', True, -3.789400003506582e-08), ('pr49_v4c:9:59:STRICT_DT_TRIGGERED_V4C', True, -3.101876829003647e-08), ('paused_paired20:111:287:ORIGINAL_SAFER_BASELINE', True, 1.361013186595983e-07), ('paused_paired20:111:287:STRICT_DT_TRIGGERED_V4C', True, 1.1908204008426182e-06)].
- Per-trajectory primary classifications: [('paused_paired20:111:287:ORIGINAL_SAFER_BASELINE', 'EARLY_SAFETY_PROXY_STOP', 'PROXY_ONLY_NOT_CERTIFIED'), ('paused_paired20:111:287:STRICT_DT_TRIGGERED_V4C', 'CBF_BOUNDARY_STALL', None), ('pr47_g1_baseline:0:50:ORIGINAL_SAFER_BASELINE', 'EARLY_SAFETY_PROXY_STOP', 'CERTIFIED_ROBUST_OVERLAP'), ('pr49_v4c:0:50:STRICT_DT_TRIGGERED_V4C', 'CBF_BOUNDARY_STALL', None), ('pr49_v4c:1:51:ORIGINAL_SAFER_BASELINE', 'EARLY_SAFETY_PROXY_STOP', 'PROXY_ONLY_NOT_CERTIFIED'), ('pr49_v4c:1:51:STRICT_DT_TRIGGERED_V4C', 'CBF_BOUNDARY_STALL', None), ('pr49_v4c:8:58:ORIGINAL_SAFER_BASELINE', 'CBF_BOUNDARY_STALL', None), ('pr49_v4c:8:58:STRICT_DT_TRIGGERED_V4C', 'CBF_BOUNDARY_STALL', None), ('pr49_v4c:9:59:ORIGINAL_SAFER_BASELINE', 'EARLY_SAFETY_PROXY_STOP', 'PROXY_ONLY_NOT_CERTIFIED'), ('pr49_v4c:9:59:STRICT_DT_TRIGGERED_V4C', 'CBF_BOUNDARY_STALL', None)].
- Primary counts: {'EARLY_SAFETY_PROXY_STOP': 4, 'CBF_BOUNDARY_STALL': 6}; secondary counts: {'BASELINE_LIMITATION_PRESERVED': 4, 'TRIGGER_NEUTRAL_BASELINE_EQUIVALENT': 2}.
- Nominal/CBF attribution: [('pr47_g1_baseline:0:50:ORIGINAL_SAFER_BASELINE', False, False), ('pr49_v4c:0:50:STRICT_DT_TRIGGERED_V4C', False, True), ('pr49_v4c:1:51:ORIGINAL_SAFER_BASELINE', False, True), ('pr49_v4c:1:51:STRICT_DT_TRIGGERED_V4C', False, True), ('pr49_v4c:8:58:ORIGINAL_SAFER_BASELINE', False, True), ('pr49_v4c:8:58:STRICT_DT_TRIGGERED_V4C', False, True), ('pr49_v4c:9:59:ORIGINAL_SAFER_BASELINE', False, True), ('pr49_v4c:9:59:STRICT_DT_TRIGGERED_V4C', False, True), ('paused_paired20:111:287:ORIGINAL_SAFER_BASELINE', False, True), ('paused_paired20:111:287:STRICT_DT_TRIGGERED_V4C', False, True)].
- Oscillation-supported trajectories: [].
- Goal-tolerance-limited and horizon-limited labels are offline classifications only; no horizon/tolerance was changed and no arrival was extrapolated.

## Evidence limits

- PR #47's 0->50 baseline proxy stop has saved PR #48 float64 robust-overlap certification. Other proxy stops remain proxy-only unless an existing matching certification is present.
- Source A lacks saved nominal/safe controls; its state is reconstructed only from saved executed controls and frozen explicit Euler, so CBF-attribution claims for that record remain unavailable.
- The scheduler race is preserved exactly: sequence 3 briefly entered, produced no terminal or step file, and is excluded from all trajectory statistics.
- Unique recommended next task: `A separately authorized controller-navigation study`.
