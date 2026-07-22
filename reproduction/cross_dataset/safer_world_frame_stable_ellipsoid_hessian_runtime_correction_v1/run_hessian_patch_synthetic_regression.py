"""Post-patch forward and world-Hessian regression without controller paths."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,torch
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m.distance_point_ellipsoid
def qrot(q):
 q=q/np.linalg.norm(q,axis=1)[:,None];w,x,y,z=q.T;return np.stack((np.stack((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),1),np.stack((2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),1),np.stack((2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)),1)),1)
def ref(a,u):
 aa=a*a;q=(u*u/aa).sum(1)-1;outside=q>=0;lo=np.where(outside,0.,-(a.min(1)**2)*(1-1e-15));hi=np.where(outside,np.maximum(np.linalg.norm(a*u/(a.min(1)[:,None]**2),axis=1),1.),0.)
 for _ in range(30):f=(aa*u*u/(hi[:,None]+aa)**2).sum(1)-1;hi=np.where(outside&(f>0),hi*2,hi)
 for _ in range(240):m=(lo+hi)*.5;f=(aa*u*u/(m[:,None]+aa)**2).sum(1)-1;lo=np.where(f>=0,m,lo);hi=np.where(f>=0,hi,m)
 lam=(lo+hi)*.5;phi=np.where(outside,1.,-1.);d=lam[:,None]+aa;D=aa/d;v=-aa*u/d**2;Fl=-2*(aa*u*u/d**3).sum(1);Fu=2*aa*u/d**2;dl=-Fu/Fl[:,None];J=np.eye(3)[None]*D[:,None,:]+np.einsum('ni,nj->nij',v,dl);return 2*phi[:,None,None]*(np.eye(3)[None]-J)
def stats(x):return {'median':float(np.median(x)),'p99':float(np.quantile(x,.99)),'max':float(np.max(x))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--old',type=Path,required=True);p.add_argument('--new',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();old,new=load('old',a.old),load('new',a.new);torch.manual_seed(20260722);sc=torch.rand(4096,3,device='cuda:0').mul_(.25).add_(.001);sc,_=torch.sort(sc,dim=-1,descending=True);u=torch.randn(4096,3,device='cuda:0').mul_(.7);od,og,_,oy=old(sc,u);nd,ng,nh,ny=new(sc,u)
 rng=np.random.default_rng(20260716);qq=rng.normal(size=(4096,4));R=qrot(qq);un=u.cpu().numpy().astype(np.float64);an=sc.cpu().numpy().astype(np.float64);_,_,nh_abs,_=new(sc,torch.abs(u));phi=np.where(((un/an)**2).sum(1)>=1.,1.,-1.);Habs=nh_abs.detach().cpu().numpy().astype(np.float64)*phi[:,None,None];flip=np.where(un<0,-1.,1.);Hs=flip[:,:,None]*Habs*flip[:,None,:];Hw=np.einsum('nij,njk,nlk->nil',R,Hs,R);HrefL=ref(an,un);Href=np.einsum('nij,njk,nlk->nil',R,HrefL,R);err=np.linalg.norm(Hw-Href,axis=(1,2))/(1+np.linalg.norm(Href,axis=(1,2)));sym=np.linalg.norm(Hw-Hw.swapaxes(1,2),axis=(1,2))/(1+np.linalg.norm(Hw,axis=(1,2)));dirs=rng.normal(size=(32,3));dirs/=np.linalg.norm(dirs,axis=1)[:,None];hv=np.concatenate([np.linalg.norm(Hw@v-Href@v,axis=1)/(1+np.linalg.norm(Href@v,axis=1)) for v in dirs])
 z=torch.tensor([[1e-8,.13,.09],[1e-10,.13,.09],[0.,.13,.09],[-1e-8,.13,-.09],[.13,1e-8,.09],[.13,.09,1e-8]],device='cuda:0');az=torch.tensor([[.2,.1,.05]]*6,device='cuda:0');_,_,hz,_=new(az,torch.abs(z+1e-8));zero_finite=torch.isfinite(hz).reshape(6,-1).all(dim=1);out={'forward_h_bitwise_exact':bool(torch.equal(od,nd)),'forward_grad_bitwise_exact':bool(torch.equal(og,ng)),'closest_point_bitwise_exact':bool(torch.equal(oy,ny)),'regular_case_count':4096,'hessian_error':stats(err),'hvp_error':stats(hv),'symmetry_max':float(sym.max()),'finite_ratio':float(np.isfinite(Hw).all(axis=(1,2)).mean()),'zero_component_finite_count':int(zero_finite.sum().item()),'zero_component_total':6,'status':'PASS_WORLD_FRAME_STABLE_HESSIAN_SYNTHETIC_REGRESSION' if torch.equal(od,nd) and torch.equal(og,ng) and torch.equal(oy,ny) and stats(err)['max']<=1e-2 and stats(hv)['max']<=1e-2 and int(zero_finite.sum().item())==6 else 'FAIL'};a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
