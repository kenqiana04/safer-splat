"""Float64 KKT Hessian references; intentionally independent of frozen runtime."""
from __future__ import annotations
import numpy as np

def root_bisect(a,u,iters=240):
    aa=a*a; q=float(np.sum((u/a)**2)-1.0)
    if q >= 0:
        lo=0.; hi=max(float(np.linalg.norm(a*u/(a.min()**2))),1.)
        while np.sum(aa*u*u/(hi+aa)**2)-1 > 0: hi*=2
        phi=1.
    else:
        lo=-(a.min()**2)*(1-1e-15); hi=0.; phi=-1.
        if np.sum(aa*u*u/(lo+aa)**2)-1 <= 0: raise ValueError('nonunique projection')
    for _ in range(iters):
        mid=(lo+hi)*.5; f=float(np.sum(aa*u*u/(mid+aa)**2)-1)
        if f>=0: lo=mid
        else: hi=mid
        if hi-lo<=1e-14: break
    return (lo+hi)*.5,phi

def root_newton(a,u):
    aa=a*a; q=float(np.sum((u/a)**2)-1.0)
    if q>=0:
        lo=0.;hi=max(float(np.linalg.norm(a*u/(a.min()**2))),1.);phi=1.
        while np.sum(aa*u*u/(hi+aa)**2)-1>0:hi*=2
    else:
        lo=-(a.min()**2)*(1-1e-15);hi=0.;phi=-1.
    lam=(lo+hi)*.5
    for _ in range(100):
        f=float(np.sum(aa*u*u/(lam+aa)**2)-1); fp=float(-2*np.sum(aa*u*u/(lam+aa)**3))
        if abs(f)<=1e-13: break
        nxt=lam-f/fp if fp else np.nan
        if not (lo<nxt<hi) or not np.isfinite(nxt):nxt=(lo+hi)*.5
        if f>=0:lo=lam
        else:hi=lam
        lam=nxt
    for _ in range(80):
        m=(lo+hi)*.5
        if np.sum(aa*u*u/(m+aa)**2)-1>=0:lo=m
        else:hi=m
    return (lo+hi)*.5,phi

def root_25(a,u):
    """Frozen-count bisection in the equivalent dimensional KKT variable."""
    aa=a*a;q=float(np.sum((u/a)**2)-1.0)
    if q>=0:
        lo=0.;hi=max(float(np.linalg.norm(a*u/(a.min()**2))),1.);phi=1.
        while np.sum(aa*u*u/(hi+aa)**2)-1>0:hi*=2
    else:
        lo=-(a.min()**2)*(1-1e-15);hi=0.;phi=-1.
    for _ in range(25):
        mid=(lo+hi)*.5
        if np.sum(aa*u*u/(mid+aa)**2)-1>=0:lo=mid
        else:hi=mid
    return mid,phi

def implicit_local(a,u,solver=root_bisect):
    lam,phi=solver(a,u);aa=a*a;den=lam+aa;y=aa*u/den
    D=aa/den;v=-aa*u/(den*den);Fl=-2*np.sum(aa*u*u/(den**3));Fu=2*aa*u/(den*den);dl=-Fu/Fl
    J=np.diag(D)+np.outer(v,dl);H=2*phi*(np.eye(3)-J)
    g=2*phi*(u-y);kkt=float(np.linalg.norm(y-u+lam*y/aa)/max(1,np.linalg.norm(u),np.linalg.norm(y),abs(lam)))
    return H,g,y,lam,phi,kkt

def envelope_world(a,R,x,solver=root_bisect):
    u=R.T@x;H,g,_,_,_,_=implicit_local(a,u,solver);return R@H@R.T,R@g

def fd_hessian_world(a,R,x):
    cols=[];allh=[]
    for fac in (1.,.5,2.):
        cols=[]
        for j in range(3):
            e=max(1e-5,1e-4*(1+abs(float(x[j]))))*fac;vals=[]
            for k in (2.,1.,-1.,-2.):
                z=x.copy();z[j]+=k*e;vals.append(envelope_world(a,R,z,root_newton)[1])
            cols.append((-vals[0]+8*vals[1]-8*vals[2]+vals[3])/(12*e))
        allh.append(np.stack(cols,axis=1))
    stable=all(np.linalg.norm(h-allh[0])/(1+np.linalg.norm(allh[0]))<=1e-4 for h in allh[1:])
    return allh[0],stable

def nerr(A,B):return float(np.linalg.norm(A-B)/(1+np.linalg.norm(B)))
def sym(A):return float(np.linalg.norm(A-A.T)/(1+np.linalg.norm(A)))
