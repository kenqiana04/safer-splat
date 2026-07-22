"""Functional, non-inplace autograd parity for active frozen-query ellipsoids."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np,torch
from splat.gsplat_utils import DummyGSplatLoader
from ellipsoids.covariance_utils import quaternion_to_rotation_matrix
def points(path):
 d=json.loads(Path(path).read_text());c=np.asarray([f['transform_matrix'] for f in d['frames']],np.float32)[:,:3,3];lo=np.array([-6.322019100189209,-6.241601943969727,-5.377645492553711],np.float32);hi=np.array([6.019745826191,6.639648914337158,6.109530925750732],np.float32);r=[x.copy() for x in c]
 for i in np.linspace(0,299,30,dtype=int):
  for a in range(3):
   for m in (.05,.1,.2):
    for z in (-1.,1.):x=c[i].copy();x[a]+=z*m;r.append(x)
 ax=[np.linspace(c[:,i].min(),c[:,i].max(),4,dtype=np.float32) for i in range(3)];r.extend(np.stack(np.meshgrid(*ax,indexing='ij'),axis=-1).reshape(-1,3));e=hi-lo
 for z in ((-1,-1,-1),(-1,1,1),(1,-1,1),(1,1,-1)):r.append(np.where(np.array(z)<0,lo-.1*e,hi+.1*e).astype(np.float32))
 x=np.asarray(r,np.float32);assert hashlib.sha256(x.tobytes()).hexdigest()=='5d0b971c40adc27915a23c1c5da7cc2b260edb07e0f8d6c223fdd8736519d5d2';return x
def f(loader,x,i):
 R=quaternion_to_rotation_matrix(loader.rots[i:i+1]);s,ind=torch.sort(loader.scales[i:i+1],dim=-1,descending=True);R=torch.gather(R,2,ind[...,None,:].expand_as(R));v=torch.bmm(R.transpose(1,2),(x-loader.means[i]).view(1,3,1)).view(1,3)+1e-8;sign=torch.sign(v);v=torch.abs(v);axes=s+1e-8;z=v/axes;r=(axes/axes[:,-1:])**2;n=r*z;low=z[:,-1]-1;up=torch.where((z*z).sum(-1)>=1,torch.linalg.vector_norm(n,dim=-1)-1,torch.zeros_like(low))
 for _ in range(25):
  lam=(low+up).mul(.5).unsqueeze(-1);g=((n/(lam+r))**2).sum(-1)-1;low=torch.where(g>=0,lam[:,0],low);up=torch.where(g>=0,up,lam[:,0])
 yhat=r*v/(lam+r);dist=((yhat-v)**2).sum(-1);phi=torch.sign(((1/s)**2*v**2).sum(-1)-1);return phi*dist
def main():
 p=argparse.ArgumentParser();p.add_argument('--canonical',type=Path,required=True);p.add_argument('--transforms',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--method');a=p.parse_args();c=a.canonical;d=DummyGSplatLoader('cuda:0');d.initialize_attributes(torch.from_numpy(np.load(c/'means_world_m.npy')),torch.from_numpy(np.load(c/'quaternions_wxyz.npy')),torch.from_numpy(np.load(c/'scales_linear_m.npy')));rows=[]
 for q in points(a.transforms):
  x=torch.from_numpy(q).cuda();h,_,_,_=d.query_distance(x,distance_type='ball-to-ellipsoid',radius=0.);i=int(h.argmin());xa=x.detach().clone().requires_grad_(True);v=f(d,xa,i);g=torch.autograd.grad(v,xa)[0];rows.append((float(h[i]),float(v.detach()),g.detach().cpu().numpy(),i))
 vals=np.array([x[0] for x in rows]);fun=np.array([x[1] for x in rows]);gr=np.stack([x[2] for x in rows]);out={'method':a.method,'functional_autograd':True,'finite_count':int(np.isfinite(gr).all(1).sum()),'nonfinite_count':int((~np.isfinite(gr).all(1)).sum()),'functional_h_max_abs_diff_vs_official':float(np.abs(vals-fun).max()),'gradient_norm_min':float(np.linalg.norm(gr,axis=1).min()),'gradient_norm_max':float(np.linalg.norm(gr,axis=1).max()),'status':'PASS' if np.isfinite(gr).all() and np.abs(vals-fun).max()<=1e-6 else 'FAIL'};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
