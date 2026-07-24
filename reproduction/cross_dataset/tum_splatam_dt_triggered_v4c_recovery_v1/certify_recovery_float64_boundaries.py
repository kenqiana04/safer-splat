#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1');MAP=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a');R=.015
def rot(q):
 w,x,y,z=q/np.linalg.norm(q);return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def solve(a,z,newton):
 a2=a*a;f=lambda l:float(np.sum((a*z/(l+a2))**2)-1);inside=np.sum((z/a)**2)<1;lo,hi=((-a2.min()*(1-1e-14),0.) if inside else (0.,1.))
 while not inside and f(hi)>0:hi*=2
 l=(lo+hi)/2
 for _ in range(160):
  if newton:
   d=-2*np.sum((a*z)**2/(l+a2)**3);n=l-f(l)/d
   if lo<n<hi:l=n
  if f(l)>0:lo=l
  else:hi=l
  l=(lo+hi)/2
 y=a2*z/(l+a2);return y,abs(f(l))
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();d=Path(a.run);rows=json.loads((d/'steps.json').read_text());m=np.load(MAP/'means_world_m.npy',mmap_mode='r');s=np.load(MAP/'scales_linear_m.npy',mmap_mode='r');q=np.load(MAP/'quaternions_wxyz.npy',mmap_mode='r');select=set()
 for i,r in enumerate(rows):
  if r['strict_trigger'] or r['recovery_active'] or r['next_h']<0:select.update(range(max(0,i-3),min(len(rows),i+4)))
 select.update(range(max(0,len(rows)-4),len(rows)));mn=min(range(len(rows)),key=lambda i:rows[i]['next_h']);select.update(range(max(0,mn-3),min(len(rows),mn+4)))
 out=[]
 for i in sorted(select):
  r=rows[i];idx=r['active_gaussian'];x=np.asarray(r['state'][:3],float);z=rot(q[idx].astype(float)).T@(x-m[idx].astype(float));phi=1. if np.sum((z/s[idx])**2)>=1 else -1.;ya,ka=solve(s[idx].astype(float),z,False);yb,kb=solve(s[idx].astype(float),z,True);ha=phi*np.sum((ya-z)**2)-R*R;hb=phi*np.sum((yb-z)**2)-R*R;t=max(1e-12,10*abs(ha-hb),10*max(ka,kb));out.append({'step':i,'h_float32':r['current_h'],'h_ref_a':ha,'h_ref_b':hb,'tau_ref':t,'kkt_residual_max':max(ka,kb),'classification':'ROBUST_OVERLAP' if ha<-t else 'ROBUST_SAFE' if ha>t else 'NUMERICALLY_INDETERMINATE'})
 data={'run':str(d),'certified_steps':out,'min_h_ref':min(x['h_ref_a'] for x in out),'robust_overlap_count':sum(x['classification']=='ROBUST_OVERLAP' for x in out),'max_residual':max(x['kkt_residual_max'] for x in out)};o=ROOT/'float64_certification';o.mkdir(exist_ok=True);(o/(d.name+'_float64.json')).write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
if __name__=='__main__':main()
