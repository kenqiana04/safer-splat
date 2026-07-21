"""Static contract tests for the frozen tuned-surface 2x2 ablation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
def tree(root):
 d=hashlib.sha256()
 for p in sorted(root.rglob("*.py")): d.update(p.relative_to(root).as_posix().encode()+b"\0"+p.read_bytes())
 return d.hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--baseline",type=Path,required=True); p.add_argument("--variants",type=Path,required=True); p.add_argument("--prior",type=Path,required=True); p.add_argument("--targets",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); prior=np.load(a.prior,allow_pickle=False); valid=prior["prior_valid"].astype(bool); q=prior["quats_wxyz"]; scales=np.exp(prior["log_scales"])
 checks={"s0_source_identical":tree(a.baseline)==tree(a.variants/"S0_TUNED_BASELINE"),"seed_count_359140":len(prior["xyz"])==359140,"prior_valid_fraction":float(valid.mean())>=.995,"quaternion_wxyz_unit":float(np.max(abs(np.linalg.norm(q,axis=1)-1)))<2e-6,"positive_scales":bool((scales>0).all()),"normal_thickness_rule":bool((scales[:,2]<=.35*np.minimum(scales[:,0],scales[:,1])+1e-7).all()),"train_targets_240":len(list(a.targets.glob("*.npz")))==240,"no_eval_target_path":not any("eval" in str(x).lower() for x in a.targets.glob("*.npz"))}
 result={"checks":checks,"status":"PASS" if all(checks.values()) else "FAIL"}; a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
