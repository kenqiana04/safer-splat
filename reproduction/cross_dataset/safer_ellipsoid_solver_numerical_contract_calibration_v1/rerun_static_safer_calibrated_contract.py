"""Static-only frozen-map audit using raw frozen solver modules, not checkout files."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import torch

def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def stats(x):
    x=np.asarray(x,dtype=np.float64);return {'min':float(x.min()),'median':float(np.median(x)),'p95':float(np.quantile(x,.95)),'max':float(x.max())}
def frozen_dummy(distances:Path, gsplat:Path):
    import splat
    dspec=importlib.util.spec_from_file_location('splat.distances',distances);dm=importlib.util.module_from_spec(dspec);assert dspec.loader;dspec.loader.exec_module(dm);sys.modules['splat.distances']=dm
    gspec=importlib.util.spec_from_file_location('frozen_gsplat_utils',gsplat);gm=importlib.util.module_from_spec(gspec);assert gspec.loader;gspec.loader.exec_module(gm);return gm.DummyGSplatLoader
def load_arrays(root:Path, method:str):
    if method=='SPLATAM': return [np.load(root/n) for n in ('means_world_m.npy','quaternions_wxyz.npy','scales_linear_m.npy')]
    parts=[root/f'submap_{i:02d}' for i in range(25)]
    return [np.concatenate([np.load(p/n) for p in parts],axis=0) for n in ('means_world_m.npy','quaternions_wxyz.npy','scales_linear_m.npy')]
def points(transforms:Path):
    data=json.loads(transforms.read_text());cam=np.asarray([f['transform_matrix'] for f in data['frames']],dtype=np.float32)[:,:3,3]
    lo=np.array([-6.322019100189209,-6.241601943969727,-5.377645492553711],np.float32);hi=np.array([6.019745826721191,6.639648914337158,6.109530925750732],np.float32);r=[x.copy() for x in cam]
    for i in np.linspace(0,299,30,dtype=int):
      for axis in range(3):
       for mag in (.05,.10,.20):
        for sign in (-1.,1.):x=cam[i].copy();x[axis]+=sign*mag;r.append(x)
    axes=[np.linspace(cam[:,d].min(),cam[:,d].max(),4,dtype=np.float32) for d in range(3)];r.extend(np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3));ext=hi-lo
    for sign in ((-1,-1,-1),(-1,1,1),(1,-1,1),(1,1,-1)):r.append(np.where(np.array(sign)<0,lo-.1*ext,hi+.1*ext).astype(np.float32))
    q=np.asarray(r,np.float32);assert q.shape==(908,3) and sha_bytes(q.tobytes())=='5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2';return q
def main():
 p=argparse.ArgumentParser();p.add_argument('--method',choices=['SPLATAM','GAUSSIAN_SLAM'],required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--transforms',type=Path,required=True);p.add_argument('--distances',type=Path,required=True);p.add_argument('--gsplat',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 means,rots,scales=load_arrays(a.root,a.method);q=points(a.transforms);Dummy=frozen_dummy(a.distances,a.gsplat);d=Dummy('cuda:0');d.initialize_attributes(torch.from_numpy(means),torch.from_numpy(rots),torch.from_numpy(scales))
 def once(top=False):
  vals=[];gr=[];idx=[];tops=[]
  for x in q:
   h,g,_,_=d.query_distance(torch.from_numpy(x).cuda(),distance_type='ball-to-ellipsoid',radius=0.); ids=torch.topk(h,k=8,largest=False).indices; i=int(ids[0]);vals.append(float(h[i]));gr.append(g[i].detach().cpu().numpy());idx.append(i);tops.append([int(z) for z in ids.detach().cpu().tolist()])
  return np.asarray(vals),np.asarray(gr),idx,tops
 start=time.time();A,gA,iA,tops=once(True);B,gB,iB,_=once();C,gC,iC,_=once();torch.cuda.synchronize();delta=np.abs(A[1:300]-A[:299]);out={'method':a.method,'frozen_query_contract':'raw blobs supplied at invocation; official ball-to-ellipsoid float32 25-step h and analytical envelope grad','gaussian_count':int(len(means)),'query_count':908,'query_sha256':sha_bytes(q.tobytes()),'no_filtering':True,'runs_finite':bool(np.isfinite(A).all() and np.isfinite(B).all() and np.isfinite(C).all()),'h_statistics':stats(A),'negative_count':int((A<0).sum()),'active_indices_deterministic':iA==iB==iC,'gradient_finite':bool(np.isfinite(gA).all() and np.isfinite(gB).all()),'gradient_repeat_exact':bool(np.array_equal(gA,gB)),'exact_deterministic':bool(np.array_equal(A,B) and np.array_equal(A,C)),'continuity':{'pair_count':299,'threshold':.1,'abs_delta_h':stats(delta),'status':'PASS' if bool(np.isfinite(delta).all() and not np.any(delta>.1)) else 'FAIL'},'active_top8_recorded':len(tops)==908,'runtime_seconds':time.time()-start,'peak_gpu_memory_bytes':int(torch.cuda.max_memory_allocated())}
 out['status']=('PASS' if out['runs_finite'] and out['exact_deterministic'] and out['gradient_finite'] and out['gradient_repeat_exact'] and out['continuity']['status']=='PASS' else 'FAIL');a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
