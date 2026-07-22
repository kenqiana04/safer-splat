"""Exact static-only query audit; no map mutation, optimizer, or controller."""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import torch
from splat.gsplat_utils import DummyGSplatLoader
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def stats(x):
 x=np.asarray(x,dtype=np.float64);return {'min':float(x.min()),'median':float(np.median(x)),'mean':float(x.mean()),'p95':float(np.quantile(x,.95)),'max':float(x.max())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--canonical',type=Path,required=True);p.add_argument('--transforms',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--method',required=True);a=p.parse_args()
 c=a.canonical;means=np.load(c/'means_world_m.npy');q=np.load(c/'quaternions_wxyz.npy');s=np.load(c/'scales_linear_m.npy');data=json.loads(a.transforms.read_text());cam=np.asarray([f['transform_matrix'] for f in data['frames']],dtype=np.float32)[:,:3,3]
 lo=np.array([-6.322019100189209,-6.241601943969727,-5.377645492553711],np.float32);hi=np.array([6.019745826721191,6.639648914337158,6.109530925750732],np.float32);recs=[x.copy() for x in cam]
 for i in np.linspace(0,299,30,dtype=int):
  for axis in range(3):
   for mag in (.05,.10,.20):
    for sign in (-1.,1.): x=cam[i].copy();x[axis]+=sign*mag;recs.append(x)
 axes=[np.linspace(cam[:,d].min(),cam[:,d].max(),4,dtype=np.float32) for d in range(3)];recs.extend(np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3))
 ext=hi-lo
 for sign in ((-1,-1,-1),(-1,1,1),(1,-1,1),(1,1,-1)):recs.append(np.where(np.array(sign)<0,lo-.1*ext,hi+.1*ext).astype(np.float32))
 points=np.asarray(recs,np.float32);assert points.shape==(908,3);assert sha_bytes(points.tobytes())=='5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2'
 d=DummyGSplatLoader('cuda:0');d.initialize_attributes(torch.from_numpy(means),torch.from_numpy(q),torch.from_numpy(s))
 def once():
  vals=[];grads=[];inds=[]
  for x in points:
   h,g,_,_=d.query_distance(torch.from_numpy(x).cuda(),distance_type='ball-to-ellipsoid',radius=0.0);i=int(torch.argmin(h));vals.append(float(h[i]));grads.append(g[i].detach().cpu().numpy());inds.append(i)
  return np.asarray(vals,np.float32),np.asarray(grads,np.float32),inds
 start=time.time();A,gA,iA=once();B,gB,iB=once();C,gC,iC=once();torch.cuda.synchronize();delta=np.abs(A[1:300]-A[:299]);out={'method':a.method,'query_count':908,'query_sha256':sha_bytes(points.tobytes()),'runs_finite':bool(np.isfinite(A).all() and np.isfinite(B).all() and np.isfinite(C).all()),'exact_deterministic':bool(np.array_equal(A,B) and np.array_equal(A,C) and iA==iB==iC),'h_statistics':stats(A),'negative_count':int((A<0).sum()),'active_indices_deterministic':iA==iB==iC,'gradient_source':'official GSplatLoader analytic query gradient; functional autograd gate not yet claimed','gradient_finite':bool(np.isfinite(gA).all() and np.isfinite(gB).all()),'gradient_repeat_exact':bool(np.array_equal(gA,gB)),'gradient_norm_statistics':stats(np.linalg.norm(gA,axis=1)),'continuity':{'pair_count':299,'threshold':.1,'abs_delta_h_statistics':stats(delta),'outlier_indices':np.where(delta>.1)[0].astype(int).tolist(),'status':'PASS' if np.isfinite(delta).all() and not np.any(delta>.1) else 'BLOCKING_ANOMALY'},'runtime_seconds':time.time()-start,'no_filtering':True,'gaussian_count':int(len(means))};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
def sha_bytes(x):return hashlib.sha256(x).hexdigest()
if __name__=='__main__':main()
