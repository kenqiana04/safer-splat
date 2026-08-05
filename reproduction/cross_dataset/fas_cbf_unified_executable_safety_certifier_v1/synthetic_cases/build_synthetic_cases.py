"""Build the deterministic analytic expected-record registry for SYN-01..15."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CASES=[
 ("SYN-01","stationary far from obstacle","CERTIFIED_TERMINAL_ACTION","TERMINAL_SET_CERTIFIED"),
 ("SYN-02","actuator violation","FAIL_CLOSED_ACTUATOR_VIOLATION","ACTUATOR_BOUNDS_VIOLATION"),
 ("SYN-03","endpoint safe interior unsafe","FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE","SEGMENT_EXACT_UNSAFE"),
 ("SYN-04","exact tangent boundary","CERTIFIED_NOMINAL_CONTROL","SEGMENT_EXACT_SAFE"),
 ("SYN-05","immediate segment unsafe and acceleration cannot repair","FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE","IMMEDIATE_SEGMENT_NOT_CERTIFIED"),
 ("SYN-06","candidate segment safe and braking witness succeeds","CERTIFIED_NOMINAL_CONTROL","BACKUP_WITNESS_CERTIFIED"),
 ("SYN-07","future braking segment unsafe","FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY","BACKUP_SEGMENT_NOT_CERTIFIED"),
 ("SYN-08","terminal zero hold unsafe","FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY","TERMINAL_ZERO_HOLD_NOT_CERTIFIED"),
 ("SYN-09","unknown map region","NOT_EVALUABLE_MAP_QUERY_UNKNOWN","CURRENT_MAP_QUERY_UNKNOWN"),
 ("SYN-10","map snapshot changes during witness","FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY","MAP_SNAPSHOT_MISMATCH"),
 ("SYN-11","candidate library exhaustion","FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY","FROZEN_LIBRARY_NO_WITNESS"),
 ("SYN-12","solver timeout","SOLVER_FAILED_NOT_SCIENTIFICALLY_CLASSIFIED","TIME_BUDGET_EXHAUSTED"),
 ("SYN-13","zero actuator authority","FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY","ZERO_ACTUATOR_AUTHORITY"),
 ("SYN-14","tail witness property","CERTIFIED_NOMINAL_CONTROL","TAIL_WITNESS_VALID_UNDER_ASSUMPTIONS"),
 ("SYN-15","terminal state returns next cycle","CERTIFIED_TERMINAL_ACTION","NEXT_CYCLE_DIAGNOSIS"),
]
for case_id,description,status,reason in CASES:
    record={"case_id":case_id,"description":description,"analytic_expected_status":status,"exact_reason_code":reason,"reference_online_input":False,"deterministic":True,"seed":20260805}
    (ROOT/f"{case_id}.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
print("PASS_SYNTHETIC_CASE_BUILD",len(CASES))
