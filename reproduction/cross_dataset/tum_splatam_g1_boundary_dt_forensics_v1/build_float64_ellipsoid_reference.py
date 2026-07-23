#!/usr/bin/env python3
import json,math
from pathlib import Path
import numpy as np
ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1'); BASE=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a'); R=.015; idx=4610535
def rot(q):
 w,x,y,z=q/np.linalg.norm(q);return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def solve(a,z,newton=False):
 s2=a*a; f=lambda l:np.sum((a*z/(l+s2))**2)-1; inside=np.sum((z/a)**2)<1
 lo=(-s2.min()*(1-1e-14) if inside else 0.);hi=(0. if inside else 1.)
 while not inside and f(hi)>0:hi*=2
 l=(lo+hi)/2
 for _ in range(200):
  if newton:
   val=f(l); der=-2*np.sum((a*z)**2/(l+s2)**3); n=l-val/der
   if lo<n<hi:l=n
  if f(l)>0:lo=l
  else:hi=l
  l=(lo+hi)/2
 y=s2*z/(l+s2);return l,y,abs(f(l)),abs(np.sum((y/a)**2)-1)
m=np.load(BASE/'means_world_m.npy',mmap_mode='r')[idx].astype(np.float64);a=np.load(BASE/'scales_linear_m.npy',mmap_mode='r')[idx].astype(np.float64);q=np.load(BASE/'quaternions_wxyz.npy',mmap_mode='r')[idx].astype(np.float64); states=np.fromfile(ROOT/'trajectory_recovery'/'trajectory_states.npy',dtype=np.float32).reshape(-1,6);x=states[773,:3].astype(np.float64);z=rot(q).T@(x-m); A=solve(a,z);B=solve(a,z,True); phi=1. if np.sum((z/a)**2)>=1 else -1.;hA=phi*np.sum((A[1]-z)**2)-R*R;hB=phi*np.sum((B[1]-z)**2)-R*R;tau=max(1e-12,10*abs(hA-hB),10*max(A[2],B[2]));out={'step':773,'active_index':idx,'h_ref_a':hA,'h_ref_b':hB,'kkt_residual_a':A[2],'kkt_residual_b':B[2],'surface_residual_a':A[3],'surface_residual_b':B[3],'tau_ref':tau,'classification':'ROBUST_OVERLAP' if hA<-tau else 'ROBUST_SAFE' if hA>tau else 'NUMERICALLY_INDETERMINATE','official_float32_h':-7.421476766467094e-10,'official_error':-7.421476766467094e-10-hA};(ROOT/'float64_reference'/'terminal_reference.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
