"""Fixed-tensor world-frame algebra only; no CBF, dynamics, or QP imports."""
import json
from pathlib import Path
import numpy as np
Q=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
H=np.array([[2.,.3,-.1],[.3,1.5,.2],[-.1,.2,.7]])
f=np.array([.4,-.2,.7]);g=np.array([.1,.8,-.3])
a=float(f@H@f);b=float(g@H@f);Hp=Q@H@Q.T
out={'f_H_f':a,'g_H_f':b,'rotation_f_H_f_abs_diff':abs(float((Q@f)@Hp@(Q@f))-a),'rotation_g_H_f_abs_diff':abs(float((Q@g)@Hp@(Q@f))-b)}
out['status']='PASS_CBF_WORLD_FRAME_ALGEBRA_SMOKE' if max(out['rotation_f_H_f_abs_diff'],out['rotation_g_H_f_abs_diff'])<=1e-6 else 'FAIL'
Path(__file__).with_name('cbf_world_frame_algebra_smoke.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
