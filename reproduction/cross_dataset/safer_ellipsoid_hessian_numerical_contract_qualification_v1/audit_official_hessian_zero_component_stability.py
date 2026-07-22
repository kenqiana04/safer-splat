"""Targeted float32 audit of `1-y/x` versus its algebraic stable form."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import torch
def main():
 p=argparse.ArgumentParser();p.add_argument('--distances',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=importlib.util.spec_from_file_location('raw',a.distances);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m)
 axes=torch.tensor([[.2,.1,.05]]*6,device='cuda:0');x=torch.tensor([[1e-8,.13,.09],[1e-10,.13,.09],[0.,.13,.09],[-1e-8,.13,-.09],[.13,1e-8,.09],[.13,.09,1e-8]],device='cuda:0');u=x+1e-8;_,_,h,y=m.distance_point_ellipsoid(axes,u);official=1-y/u
 z=u/axes;r=(axes/axes[:,-1:])**2;n=r*z;lo=z[:,-1]-1;hi=torch.where((z*z).sum(-1)>=1,torch.linalg.vector_norm(n,dim=-1)-1,torch.zeros_like(lo))
 for _ in range(25):
  lam=(lo+hi).mul(.5).unsqueeze(-1);f=((n/(lam+r))**2).sum(-1)-1;lo=torch.where(f>=0,lam[:,0],lo);hi=torch.where(f>=0,hi,lam[:,0])
 lamd=lam*(axes[:,-1:]**2);stable=lamd/(lamd+axes**2);finite=float(torch.isfinite(official).all(dim=1).float().mean());out={'case_count':6,'official_y_over_x_finite_ratio':finite,'stable_equivalent_finite_ratio':float(torch.isfinite(stable).all(dim=1).float().mean()),'classification':'OFFICIAL_Y_OVER_X_NONFINITE' if finite<1 else 'OFFICIAL_Y_OVER_X_STABLE','stable_algebraic_form_required':bool(finite<1 and torch.isfinite(stable).all()),'note':'The +1e-8 local perturbation can exactly cancel a negative component; lambda/(lambda+a^2) avoids y/x.'};a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
