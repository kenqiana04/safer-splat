"""Compare frozen Gaussian-SLAM checkpoint rendering against canonical shards."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--canonical-root',type=Path,required=True);p.add_argument('--train-adapter',type=Path,required=True);p.add_argument('--eval-adapter',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 import sys,numpy as np,torch,torch.nn as nn;sys.path.insert(0,str(a.repo));from src.entities.datasets import TUM_RGBD;from src.entities.gaussian_model import GaussianModel;from src.utils.utils import get_render_settings,render_gaussian_model
 ckpts=sorted((a.run/'submaps').glob('*.ckpt')); fields=('xyz','features_dc','features_rest','scaling','rotation','opacity')
 raw=[torch.load(x,map_location='cpu')['gaussian_params'] for x in ckpts]
 def model(parts):
  merged={k:torch.cat([x[k] for x in parts]).cuda() for k in fields};m=GaussianModel(3);m._xyz=nn.Parameter(merged['xyz'],False);m._features_dc=nn.Parameter(merged['features_dc'],False);m._features_rest=nn.Parameter(merged['features_rest'],False);m._scaling=nn.Parameter(merged['scaling'],False);m._rotation=nn.Parameter(merged['rotation'],False);m._opacity=nn.Parameter(merged['opacity'],False);return m
 original=model(raw)
 # Canonical reconstruction exactly follows the source activation inverses.
 parts=[]
 for i in range(25):
  d=a.canonical_root/f'submap_{i:02d}';sc=np.load(d/'scales_linear_m.npy');op=np.load(d/'opacities_activated.npy');parts.append({'xyz':torch.from_numpy(np.load(d/'means_world_m.npy')),'features_dc':torch.from_numpy(np.load(d/'features_dc.npy')),'features_rest':torch.from_numpy(np.load(d/'features_rest.npy')),'scaling':torch.from_numpy(np.log(sc)),'rotation':torch.from_numpy(np.load(d/'quaternions_wxyz.npy')),'opacity':torch.from_numpy(np.log(np.clip(op,1e-7,1-1e-7)/(1-np.clip(op,1e-7,1-1e-7))) )})
 canonical=model(parts);cfg={'frame_limit':240,'H':480,'W':640,'fx':517.3,'fy':516.5,'cx':318.6,'cy':255.3,'crop_edge':50,'depth_scale':5000.0,'distortion':[0.2624,-0.9531,-0.0054,0.0026,1.1633]};rows=[]
 for split,path,ids in [('train',a.train_adapter,(0,79,159,239)),('eval',a.eval_adapter,(1,9,17,25,33,41,49,57))]:
  ds=TUM_RGBD({**cfg,'input_path':str(path)})
  for idx in ids:
   _,_,_,c2w=ds[idx];rs=get_render_settings(ds.width,ds.height,ds.intrinsics,np.linalg.inv(c2w));x=render_gaussian_model(original,rs);repeat=render_gaussian_model(original,rs);y=render_gaussian_model(canonical,rs)
   rows.append({'split':split,'index':idx,'native_repeat_rgb_max_abs':float((x['color']-repeat['color']).abs().max()),'native_repeat_depth_max_abs':float((x['depth']-repeat['depth']).abs().max()),'native_repeat_alpha_max_abs':float((x['alpha']-repeat['alpha']).abs().max()),'adapter_rgb_max_abs':float((x['color']-y['color']).abs().max()),'adapter_depth_max_abs':float((x['depth']-y['depth']).abs().max()),'adapter_alpha_max_abs':float((x['alpha']-y['alpha']).abs().max()),'depth_valid_mask_exact':bool(torch.equal(x['depth']>0,y['depth']>0)),'alpha_mask_exact':bool(torch.equal(x['alpha']>0,y['alpha']>0))})
 ok=all(r['adapter_rgb_max_abs']<=max(2*r['native_repeat_rgb_max_abs'],1e-5) and r['adapter_depth_max_abs']<=max(2*r['native_repeat_depth_max_abs'],1e-5) and r['adapter_alpha_max_abs']<=max(2*r['native_repeat_alpha_max_abs'],1e-5) and r['depth_valid_mask_exact'] and r['alpha_mask_exact'] for r in rows);out={'method':'Gaussian-SLAM','train_frame_count':4,'eval_frame_count':8,'rows':rows,'status':'PASS' if ok else 'GAUSSIAN_SLAM_NATIVE_RENDER_PARITY_FAILED'};dump(a.output,out);print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
