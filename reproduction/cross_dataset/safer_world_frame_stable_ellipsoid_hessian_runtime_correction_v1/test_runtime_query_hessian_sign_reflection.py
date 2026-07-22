"""Pre-patch RF0/RFR gate against an independent float64 KKT Hessian."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

def root(a,u):
 aa=a*a;q=(u*u/aa).sum(1)-1;out=q>=0;lo=np.where(out,0.,-(a.min(1)**2)*(1-1e-15));hi=np.where(out,np.maximum(np.linalg.norm(a*u/(a.min(1)[:,None]**2),axis=1),1.),0.)
 for _ in range(30):
  f=(aa*u*u/(hi[:,None]+aa)**2).sum(1)-1;hi=np.where(out&(f>0),hi*2,hi)
 for _ in range(240):
  m=(lo+hi)*.5;f=(aa*u*u/(m[:,None]+aa)**2).sum(1)-1;lo=np.where(f>=0,m,lo);hi=np.where(f>=0,hi,m)
 return (lo+hi)*.5,np.where(out,1.,-1.)
def hess(a,u):
 lam,phi=root(a,u);aa=a*a;d=lam[:,None]+aa;D=aa/d;v=-aa*u/d**2;Fl=-2*(aa*u*u/d**3).sum(1);Fu=2*aa*u/d**2;dl=-Fu/Fl[:,None];J=np.eye(3)[None]*D[:,None,:]+np.einsum('ni,nj->nij',v,dl);return 2*phi[:,None,None]*(np.eye(3)[None]-J)
def rotations(n):
 rng=np.random.default_rng(20260716);q=rng.normal(size=(n,4));q/=np.linalg.norm(q,axis=1)[:,None];w,x,y,z=q.T;return np.stack((np.stack((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),1),np.stack((2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),1),np.stack((2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)),1)),1)
def stat(x):return {'median':float(np.median(x)),'p99':float(np.quantile(x,.99)),'max':float(np.max(x))}
def main():
 rng=np.random.default_rng(20260716);n=4096;a=np.sort(rng.uniform(.001,.25,(n,3)),axis=1)[:,::-1];u=rng.normal(size=(n,3))*.7;u[:8]=np.array([[.3*s1,.2*s2,.1*s3] for s1 in(-1,1) for s2 in(-1,1) for s3 in(-1,1)])
 R=rotations(n);Hsigned=hess(a,u);Habs=hess(a,np.abs(u));F=np.eye(3)[None]*np.where(u<0,-1.,1.)[:,None,:];ref=np.einsum('nij,njk,nlk->nil',R,Hsigned,R);rf0=np.einsum('nij,njk,nlk->nil',R,Habs,R);rfr=np.einsum('nij,njk,nlk->nil',R,F@Habs@F,R)
 err=lambda H:np.linalg.norm(H-ref,axis=(1,2))/(1+np.linalg.norm(ref,axis=(1,2)));out={'case_count':n,'sign_octants':8,'mixed_sign_general_cases':n-8,'RF0':stat(err(rf0)),'RFR':stat(err(rfr)),'RFR_finite_ratio':float(np.isfinite(rfr).all(axis=(1,2)).mean()),'RFR_symmetry_max':float(np.linalg.norm(rfr-rfr.swapaxes(1,2),axis=(1,2)).max()),'selection':'SIGN_REFLECTION_REQUIRED_AND_VERIFIED' if stat(err(rfr))['max']<=1e-2 and stat(err(rf0))['p99']>1e-3 else 'BLOCKED_BY_RUNTIME_SIGN_REFLECTION_CONTRACT'}
 Path(__file__).with_name('sign_reflection_contract.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
