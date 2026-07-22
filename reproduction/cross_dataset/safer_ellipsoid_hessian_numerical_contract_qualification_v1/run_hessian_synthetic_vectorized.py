"""Vectorized form of the fixed 4,096-case reference/FD protocol."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,torch

def rotations(seed=20260716):
 rng=np.random.default_rng(seed);q=np.empty((4096,4));q[:512]=[1,0,0,0];groups=np.array(['ROT_IDENTITY']*512,dtype=object)
 for k in range(3):q[512+128*k:512+128*(k+1)]=[np.cos(np.pi/4),*(np.eye(3)[k]*np.sin(np.pi/4))]
 groups=np.concatenate((groups,np.array(['ROT_AXIS_X']*128+['ROT_AXIS_Y']*128+['ROT_AXIS_Z']*128,dtype=object)))
 g=rng.normal(size=(24,4));g/=np.linalg.norm(g,axis=1)[:,None];q[896:]=g[np.arange(3200)%24];groups=np.concatenate((groups,np.array(['ROT_GENERAL']*3200,dtype=object)))
 w,x,y,z=q.T;R=np.stack((np.stack((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),1),np.stack((2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),1),np.stack((2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)),1)),1);return R,groups
def brackets(a,u):
 aa=a*a;q=(u*u/aa).sum(1)-1;outside=q>=0;lo=np.where(outside,0.,-(a.min(1)**2)*(1-1e-15));hi=np.where(outside,np.maximum(np.linalg.norm(a*u/(a.min(1)[:,None]**2),axis=1),1.),0.)
 for _ in range(30):
  f=(aa*u*u/(hi[:,None]+aa)**2).sum(1)-1;mask=outside&(f>0);hi[mask]*=2
 return lo,hi,np.where(outside,1.,-1.)
def bisection(a,u,n=240):
 aa=a*a;lo,hi,phi=brackets(a,u)
 for _ in range(n):
  m=(lo+hi)*.5;f=(aa*u*u/(m[:,None]+aa)**2).sum(1)-1;lo=np.where(f>=0,m,lo);hi=np.where(f>=0,hi,m)
 return (lo+hi)*.5,phi
def newton(a,u):
 aa=a*a;lo,hi,phi=brackets(a,u);lam=(lo+hi)*.5
 for _ in range(100):
  den=lam[:,None]+aa;f=(aa*u*u/den**2).sum(1)-1;fp=-2*(aa*u*u/den**3).sum(1);cand=lam-f/fp;bad=(cand<=lo)|(cand>=hi)|~np.isfinite(cand);cand=np.where(bad,(lo+hi)*.5,cand);lo=np.where(f>=0,lam,lo);hi=np.where(f>=0,hi,lam);lam=cand
 # Independent safeguarded-Newton reference: finish on its maintained legal
 # bracket so the finite-difference side is root-converged rather than merely
 # Newton-tolerance-limited.
 for _ in range(120):
  m=(lo+hi)*.5;f=(aa*u*u/(m[:,None]+aa)**2).sum(1)-1;lo=np.where(f>=0,m,lo);hi=np.where(f>=0,hi,m)
 return (lo+hi)*.5,phi
def implicit(a,u,lam,phi):
 aa=a*a;den=lam[:,None]+aa;y=aa*u/den;D=aa/den;v=-aa*u/den**2;Fl=-2*(aa*u*u/den**3).sum(1);Fu=2*aa*u/den**2;dl=-Fu/Fl[:,None];J=np.eye(3)[None]*D[:,None,:]+np.einsum('ni,nj->nij',v,dl);return 2*phi[:,None,None]*(np.eye(3)[None]-J),2*phi[:,None]*(u-y)
def ne(A,B):return np.linalg.norm(A-B,axis=(-2,-1))/(1+np.linalg.norm(B,axis=(-2,-1)))
def stat(a):return {'median':float(np.median(a)),'p99':float(np.quantile(a,.99)),'max':float(np.max(a))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--distances',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();torch.manual_seed(20260722);s=torch.rand(4096,3,device='cuda:0').mul_(.25).add_(.001);s,_=torch.sort(s,dim=-1,descending=True);u_t=torch.randn(4096,3,device='cuda:0').mul_(.7);aa=s.cpu().numpy().astype(np.float64);u=u_t.cpu().numpy().astype(np.float64);R,groups=rotations();x=np.einsum('nij,nj->ni',R,u);lam,phi=bisection(aa,u);HrefL,grefL=implicit(aa,u,lam,phi);Href=np.einsum('nij,njk,nlk->nil',R,HrefL,R);gref=np.einsum('nij,nj->ni',R,grefL)
 # Independent safeguarded-Newton envelope-gradient FD, world coordinates.
 fd=[];stable=[]
 for fac in (1.,.5,2.):
  cols=[]
  for j in range(3):
   e=np.maximum(1e-5,1e-4*(1+np.abs(x[:,j])))*fac;vals=[]
   for k in (2.,1.,-1.,-2.):
    xx=x.copy();xx[:,j]+=k*e;uu=np.einsum('nji,nj->ni',R,xx);ln,ph=newton(aa,uu);_,gg=implicit(aa,uu,ln,ph);vals.append(np.einsum('nij,nj->ni',R,gg))
   cols.append((-vals[0]+8*vals[1]-8*vals[2]+vals[3])/(12*e[:,None]))
  fd.append(np.stack(cols,2))
 Hfd=fd[0];stable=np.maximum(ne(fd[1],Hfd),ne(fd[2],Hfd))<=1e-4
 spec=importlib.util.spec_from_file_location('raw',a.distances);m=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(m);_,_,hl,_=m.distance_point_ellipsoid(s,u_t);phit=torch.sign(((u_t/s)**2).sum(-1)-1).cpu().numpy();Hoff=hl.detach().cpu().numpy().astype(np.float64)*phit[:,None,None];Hrot=np.einsum('nij,njk,nlk->nil',R,Hoff,R)
 l25,p25=bisection(aa,u,n=25);H25L,_=implicit(aa,u,l25,p25);Hstable=np.einsum('nij,njk,nlk->nil',R,H25L,R)
 dirs=np.vstack((np.eye(3),np.random.default_rng(20260716).normal(size=(32,3))));dirs/=np.linalg.norm(dirs,axis=1)[:,None]
 def pack(H):
  err=ne(H,Href);sym=np.linalg.norm(H-H.swapaxes(1,2),axis=(1,2))/(1+np.linalg.norm(H,axis=(1,2)));hv=[]
  for v in dirs:hv.append(np.linalg.norm(np.einsum('nij,j->ni',H,v)-np.einsum('nij,j->ni',Hfd,v),axis=1)/(1+np.linalg.norm(np.einsum('nij,j->ni',Hfd,v),axis=1)))
  hv=np.concatenate(hv);return {'finite_ratio':float(np.isfinite(H).all(axis=(1,2)).mean()),'error':stat(err),'hvp':stat(hv),'symmetry_max':float(sym.max())}
 out={'case_count':4096,'rotation_counts':{'ROT_IDENTITY':512,'ROT_AXIS_X':128,'ROT_AXIS_Y':128,'ROT_AXIS_Z':128,'ROT_GENERAL':3200},'reference_agreement':{'error':stat(ne(Href,Hfd)[stable]),'finite_difference_stable_count':int(stable.sum()),'finite_difference_unstable_count':int((~stable).sum()),'symmetry_max':float(np.linalg.norm(Href-Href.swapaxes(1,2),axis=(1,2)).max())},'coordinate_frame':{'identity_official':stat(ne(Hoff[groups=='ROT_IDENTITY'],Href[groups=='ROT_IDENTITY'])),'general_official_world':stat(ne(Hoff[groups=='ROT_GENERAL'],Href[groups=='ROT_GENERAL'])),'general_official_local':stat(ne(Hoff[groups=='ROT_GENERAL'],HrefL[groups=='ROT_GENERAL'])),'general_rotated_world':stat(ne(Hrot[groups=='ROT_GENERAL'],Href[groups=='ROT_GENERAL']))},'official_returned':pack(Hoff),'rotated_official':pack(Hrot),'stable_implicit_world_25':pack(Hstable)}
 def good(z):e=z['error'];h=z['hvp'];return z['finite_ratio']==1 and z['symmetry_max']<=1e-5 and e['median']<=1e-5 and e['p99']<=1e-3 and e['max']<=1e-2 and h['median']<=1e-5 and h['p99']<=1e-3 and h['max']<=1e-2
 for k in ('official_returned','rotated_official','stable_implicit_world_25'):out[k]['passes']=good(out[k])
 out['selection']='SELECT_OFFICIAL_RUNTIME_HESSIAN_CONTRACT' if out['official_returned']['passes'] else ('SELECT_ROTATED_OFFICIAL_LOCAL_HESSIAN_CONTRACT_CORE_PATCH_REQUIRED' if out['rotated_official']['passes'] else ('SELECT_STABLE_IMPLICIT_WORLD_HESSIAN_CONTRACT_CORE_PATCH_REQUIRED' if out['stable_implicit_world_25']['passes'] else 'NO_VALID_RUNTIME_HESSIAN_IMPLEMENTATION_INVALID_STOP'))
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
