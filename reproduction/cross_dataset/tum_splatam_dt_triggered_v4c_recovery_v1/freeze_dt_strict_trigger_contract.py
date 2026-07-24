#!/usr/bin/env python3
"""Write the preregistered online trigger contract without running control."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1')
H3=Path('/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1/run_shadow_dt_h1_h2_h3.py')
def main() -> None:
    data={'h3_source_path':str(H3),'h3_source_sha256':hashlib.sha256(H3.read_bytes()).hexdigest(),'online_query':'PR44-compatible float32 complete-map GSplatLoader.query_distance(ball-to-ellipsoid)','state_update':'x_next=x+0.05*[v,u]','margin_monitor_expression':'min(h(x_k+1),h(x_k+2),h(x_k+3)) < 0.0005','margin_monitor_action':'log_only','strict_trigger_expression':'current_fullmap_h > 0 and min(h(x_k+1),h(x_k+2),h(x_k+3)) < 0','recovery_entry':'Invoke frozen V4-C only when strict_trigger is true.','recovery_exit':'Historical V4-C executes its selected first control and exits after that step.','retrigger':'Recompute strict H3 after every state update; permit a new activation only if the strict expression is again true.','max_active_duration_steps':1,'fallback':'Frozen V4-C highest-min-h candidate when no candidate satisfies dt_margin; log recovery_failed.','float64_online':False,'ordinary_margin_warning_is_trigger':False}
    out=ROOT/'protocol';out.mkdir(parents=True,exist_ok=True)
    (out/'dt_trigger_contract.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
