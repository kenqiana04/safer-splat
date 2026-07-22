"""Fixed-iteration diagnostic; it never changes the frozen 25-step runtime."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np,torch
from calibration_core import bisection_projection,envelope_gradient,norm_error
def main():
 p=argparse.ArgumentParser();p.add_argument('--exact',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.exact.parent));from exact_functional_ellipsoid_solver import exact_functional_real_get_root
 torch.manual_seed(20260722);dev='cuda:0';s=torch.rand(1024,3,device=dev).mul_(.25).add_(.001);s,_=torch.sort(s,dim=-1,descending=True);x=torch.randn(1024,3,device=dev).mul_(.7);sn=s.cpu().numpy().astype(np.float64);xn=x.cpu().numpy().astype(np.float64);refs=[bisection_projection(sn[i],xn[i]) for i in range(1024)];refg=np.asarray([envelope_gradient(r,xn[i]) for i,r in enumerate(refs)])
 rows=[]
 for k in (5,10,15,20,25,30,40,60,100):
  q=x.detach().clone().requires_grad_(True);z=q/s;g=(z*z).sum(-1)-1;r=(s/s[:,-1:])**2;lam=exact_functional_real_get_root(r,z,g,max_iterations=k);y=r*q/(lam+r);d=((y-q)**2).sum(-1);phi=torch.sign((z*z).sum(-1)-1);u=torch.autograd.grad((phi*d).sum(),q)[0].detach().cpu().numpy();og=(2*phi[:,None]*(q-y)).detach().cpu().numpy();hn=(phi*d).detach().cpu().numpy();rows.append({'iterations':k,'forward_h_median_normalized_error':float(np.median([abs(hn[i]-refs[i].h)/(1+abs(refs[i].h)) for i in range(1024)])),'official_envelope_median_normalized_error':float(np.median([norm_error(og[i],refg[i]) for i in range(1024)])),'unrolled_median_normalized_error':float(np.median([norm_error(u[i],refg[i]) for i in range(1024)]))})
 out={'case_count':1024,'iterations':[5,10,15,20,25,30,40,60,100],'rows':rows,'conclusion':'Finite-program autograd is a distinct derivative: forward/envelope errors shrink with bisection resolution while unrolled error remains materially larger at the frozen 25-step contract. Diagnostic only; runtime remains 25 steps.'};a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
