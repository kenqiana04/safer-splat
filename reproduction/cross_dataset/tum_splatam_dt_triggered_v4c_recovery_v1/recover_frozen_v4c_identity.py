#!/usr/bin/env python3
"""Freeze the existing V4-C implementation identity; this script never runs it."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path('/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1')
REPO = Path('/disk1/zlab/projects/safer-splat')
SRC = REPO / 'work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py'

def main() -> None:
    data = {
        'source_path': str(SRC),
        'source_restoration_commit': 'b626b99cb1ed1437730c0e0734635fd8f0bdc517',
        'source_blob': subprocess.check_output(['git','-C',str(REPO),'hash-object',str(SRC.relative_to(REPO))], text=True).strip(),
        'source_sha256': hashlib.sha256(SRC.read_bytes()).hexdigest(),
        'recovered_horizon': 3,
        'frozen_defaults': {'num_sequences':128,'sequence_noise_scale':.15,'control_scale_list':'0,0.25,0.5,0.75,1.0','include_braking_sequences':True,'include_repulsive_sequences':True,'include_goal_directed_sequences':True,'use_cem':False,'w_base':1.0,'w_goal':.2,'w_smooth':.1,'w_safety':10.0,'dt_margin':.0005},
        'candidate_and_objective_semantics':'Existing generate_sequences/evaluate_sequences; choose lowest cost candidate with H-step min_h >= dt_margin, otherwise highest-min-h fallback.',
        'bounds':'torch.clamp each candidate and executed first control to [-0.1,0.1].',
        'entry_exit_retrigger_semantics':'Historical V4-C is stateless per step: evaluate only when activated, execute the selected first control, then exit; next step independently re-evaluates the trigger.',
        'max_active_duration_steps':1,
        'randomness':'deterministic numpy generators seeded by trial and step; CEM disabled.',
        'identity_resolved': True,
    }
    out=ROOT/'source_recovery'; out.mkdir(parents=True,exist_ok=True)
    (out/'v4c_recovery_identity.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2))
if __name__ == '__main__': main()
