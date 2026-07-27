# TUM Navigation-Protocol Gap and CBF-Stall Geometry Audit V1

**Status:** `PASS_TUM_NAVIGATION_PROTOCOL_GAP_OFFLINE_AUDIT_WITH_TUM_CAMERA_PAIR_NOT_VALID_DIRECT_NAVIGATION_TASK`.

## Scope and evidence boundary

- This is an offline-only audit of frozen source, map queries, saved states, and recorded camera centres.
- No rollout, closed-loop update, online QP solve, V4-C execution, controller change, or paired20 resume occurred.
- Direct lines, recorded camera paths, offline waypoint graphs, and saved robot trajectories are separate evidence classes.

## Original SAFER navigation stack

- Classification: `DIRECT_GOAL_ONLY` from `run.py at authoritative f63 checkout` (blob `361f09fc8f37e4713ea2fc8975d82d56cb9be46a`).
- Start construction: deterministic circle positions; goal construction: antipodal deterministic circle positions; start-goal validation: False.
- Planner=False; waypoint=False; reference trajectory=False; line-of-sight validation=False; connectivity validation=False.
- Desired controller receives the final goal directly: clamped PD acceleration directly to final goal. Success semantics: goal when stopped within 0.001; timeout while moving recorded as loose success.

## TUM task protocol and protocol difference

- TUM pairs are camera centres from frozen transforms. Filters: ['INITIAL_SAFE', 'goal_h > 0', 'separation >= 0.50m', 'finite', 'bbox valid'].
- TUM direct-line checked=False; connectivity checked=False; intermediate safety checked=False; camera path used as reference=False.
- TUM controller target=final goal only; local goal=False; waypoint update=False.
- Major task differences: ['start_sampling', 'goal_sampling', 'clearance', 'scene_assets']; critical semantic differences: []; missing original navigation layer: False.

## Direct and recorded-camera geometry

- Direct paths (257 fixed samples, radius=0.015): [('0->50', 'DIRECT_PATH_BLOCKED', -0.00025483567151241004), ('1->51', 'DIRECT_PATH_BLOCKED', -0.0002663946943357587), ('8->58', 'DIRECT_PATH_BLOCKED', -0.0008469303138554096), ('9->59', 'DIRECT_PATH_BLOCKED', -0.0018182029016315937), ('111->287', 'DIRECT_PATH_BLOCKED', -0.00025695201475173235)]
- Recorded camera paths: [('0->50', 'CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE', -0.00035400775959715247), ('1->51', 'CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE', -0.00035400775959715247), ('8->58', 'CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE', -0.00035400775959715247), ('9->59', 'CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE', -0.00035400775959715247), ('111->287', 'CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE', -0.0012862510047852993)]
- Start/goal camera endpoints safe: [('0->50', True), ('1->51', True), ('8->58', True), ('9->59', True), ('111->287', True)]; all recorded centres safe: [('0->50', False), ('1->51', False), ('8->58', False), ('9->59', False), ('111->287', False)]; full sampled camera paths safe: [('0->50', False), ('1->51', False), ('8->58', False), ('9->59', False), ('111->287', False)].
- Therefore endpoint safety does not establish an executable spherical-robot path, and a blocked direct line does not prove global unreachability.

## Saved-stall geometry and static feasible-direction diagnosis

- Six frozen CBF-boundary-stall trajectories yielded 29 specified representative states.
- Head-on barrier conflicts: 9; tangential escape available but unused: 16; multi-constraint wedges: 29; cul-de-sac indications: 8.
- Goal-directed feasible-scale proxy (active-barrier static half-space, not an online QP): min=0.129800954503, median=0.944860178757, max=1; safe controls with positive goal progress: 2/29.

## Offline waypoint feasibility

- Frozen-camera waypoint chains (33 samples per increasing-index edge): [('0->50', False, 11, 40, -0.0015698466449975967), ('1->51', False, 11, 40, -0.0005724229849874973), ('8->58', False, 11, 40, -0.0006972249830141664), ('9->59', False, 11, 40, -0.001305182813666761), ('111->287', False, 37, 170, -0.00258039147593081)].
- A waypoint graph is an offline geometric diagnostic only; it is not an executed trajectory or proof of controller completion.

## Classification and decision

- Primary classification: `TUM_CAMERA_PAIR_NOT_VALID_DIRECT_NAVIGATION_TASK`.
- Secondary findings: ['CAMERA_ENDPOINT_DIRECT_TASK_UNVALIDATED'].
- Unique next-step decision: `CLOSE_TUM_AS_SAFETY_CASE_STUDY`. paired20 remains `DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY`.

## Preserved prior evidence and claim limits

- The previously qualified SplaTAM-SAFER geometry chain, sampled-data overlap certification, and V4-C proof-of-mechanism remain prior evidence; they are not reinterpreted as navigation-completion results here.
- The current failure mode concerns navigation-task completion, not a map-query failure.
- This audit neither modifies nor tests a new controller, CBF, trigger, or filter, and it does not claim a global geometric cul-de-sac.
- Frozen paired20 manifest remains `380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6` with states {'TERMINAL_SCIENTIFIC_RESULT': 2, 'NOT_STARTED': 38}; sequence 3 terminal/steps exists=False.
- New rollout count=0; new terminal trajectory count=0; online QP count=0; V4-C count=0.
