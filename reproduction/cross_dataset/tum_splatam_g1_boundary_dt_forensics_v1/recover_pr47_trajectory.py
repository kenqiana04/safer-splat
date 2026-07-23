#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
import numpy as np
SRC=Path('/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials')
ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1')
T=Path('/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
ROOT.mkdir(parents=True,exist_ok=True); rows=json.loads((SRC/'one_trial_steps.json').read_text()); f=json.loads(T.read_text())['frames']; x=np.array([r[3] for r in f[0]['transform_matrix'][:3]]+[0,0,0],np.float32); states=[x.copy()]
for row in rows:
 u=np.asarray(row['u'],np.float32); x=x+np.float32(.05)*np.r_[x[3:],u]; states.append(x.copy())
out={'trajectory_source':'PR47_FROZEN_EXECUTION_LOG_RECONSTRUCTED_FROM_SAFE_CONTROLS','step_count':len(rows),'integrator':'x_next=x+dt*[v,u]','dt':.05,'steps_sha256':sha(SRC/'one_trial_steps.json'),'terminal_step':rows[-1]['step'],'terminal_logged_h':rows[-1]['min_h'],'terminal_active_index':rows[-1]['active'],'state_sha256':hashlib.sha256(np.asarray(states,np.float32).tobytes()).hexdigest(),'event_window':[740,773]}
(ROOT/'trajectory_recovery').mkdir(exist_ok=True);(ROOT/'trajectory_recovery'/'trajectory_states.npy').write_bytes(np.asarray(states,np.float32).tobytes());(ROOT/'trajectory_identity_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
