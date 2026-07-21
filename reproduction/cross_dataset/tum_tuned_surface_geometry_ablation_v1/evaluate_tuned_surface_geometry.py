"""Fixed-60 raw metric/RGB/Gaussian evaluator for a tuned-surface candidate."""
from __future__ import annotations
import argparse, csv, importlib.util, json, math
from pathlib import Path
import imageio.v3 as iio
import numpy as np
import torch

def load(path):
 s=importlib.util.spec_from_file_location("tuned_surface_launch",path); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
def metric(gt,pred):
 valid=(gt>0)&np.isfinite(gt)&np.isfinite(pred)&(pred>0)
 g,p=gt[valid],pred[valid]; r=p/g; t=np.maximum(r,1/r)
 return {"overlap":int(valid.sum()),"absrel":float(np.mean(abs(p-g)/g)),"sqrel":float(np.mean((p-g)**2/g)),"rmse":float(np.sqrt(np.mean((p-g)**2))),"rmse_log":float(np.sqrt(np.mean((np.log(p)-np.log(g))**2))),"d1":float(np.mean(t<1.25)),"d2":float(np.mean(t<1.25**2)),"d3":float(np.mean(t<1.25**3)),"ratio":r}
def gauss(model):
 means=model.means.detach(); scales=torch.exp(model.scales.detach()); q=model.quats.detach(); qn=torch.linalg.vector_norm(q,dim=-1); op=torch.sigmoid(model.opacities.detach()); invalid=(~torch.isfinite(scales).all(-1))|(scales<=0).any(-1)|(~torch.isfinite(q).all(-1))|(qn<=0); return {"gaussian_count":int(len(means)),"nonfinite_gaussian_count":int((~torch.isfinite(means).all(-1)).sum().item()),"invalid_scale_count":int(((~torch.isfinite(scales).all(-1))|(scales<=0).any(-1)).sum().item()),"bad_quaternion_count":int(((~torch.isfinite(q).all(-1))|(qn<=0)).sum().item()),"invalid_covariance_count":int(invalid.sum().item()),"opacity_min":float(op.min().item()),"opacity_max":float(op.max().item()),"map_bbox_min":means.min(0).values.cpu().tolist(),"map_bbox_max":means.max(0).values.cpu().tolist()}
def clean(x):
 if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)): return [clean(v) for v in x]
 return None if isinstance(x,float) and not math.isfinite(x) else x
def main():
 p=argparse.ArgumentParser(); p.add_argument("--launcher",type=Path,required=True); p.add_argument("--source",type=Path,required=True); p.add_argument("--candidate",required=True); p.add_argument("--checkpoint",type=Path,required=True); p.add_argument("--steps",type=int,required=True); p.add_argument("--prior",type=Path,required=True); p.add_argument("--targets",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); m=load(a.launcher); cfg=m.configure(a.source,a.candidate,a.out/"ephemeral",a.steps,a.prior,a.targets); cfg.load_dir=cfg.load_checkpoint=cfg.load_step=None; pipe=cfg.pipeline.setup(device="cuda:0",test_mode="test",world_size=1,local_rank=0); payload=torch.load(a.checkpoint,map_location="cpu"); pipe.load_state_dict(payload["pipeline"],strict=True); pipe.eval(); outputs=pipe.datamanager.eval_dataset._dataparser_outputs; depths=outputs.metadata["depth_filenames"]; rows=[]; ratios=[]
 with torch.no_grad():
  for i in range(len(pipe.datamanager.fixed_indices_eval_dataloader)):
   camera,batch=pipe.datamanager.fixed_indices_eval_dataloader[i]; pred=pipe.model.get_outputs_for_camera(camera.to(pipe.device))["depth"].squeeze(-1).float().cpu().numpy(); idx=int(batch["image_idx"]); gt=iio.imread(depths[idx]).astype(np.float32)*.0002; v=metric(gt,pred); ratios.append(v.pop("ratio")); rows.append({"eval_index":i,"image_idx":idx,"valid_gt":int((gt>0).sum()),**v})
 w=np.asarray([x["overlap"] for x in rows],dtype=float); summary={"candidate":a.candidate,"checkpoint":str(a.checkpoint),"checkpoint_step":int(payload["step"]),"frame_count":len(rows),"overlap":float(w.sum()/sum(x["valid_gt"] for x in rows)),"AbsRel":float(np.average([x["absrel"] for x in rows],weights=w)),"SqRel":float(np.average([x["sqrel"] for x in rows],weights=w)),"RMSE":float(np.sqrt(np.average(np.square([x["rmse"] for x in rows]),weights=w))),"RMSE_log":float(np.sqrt(np.average(np.square([x["rmse_log"] for x in rows]),weights=w))),"delta1":float(np.average([x["d1"] for x in rows],weights=w)),"delta2":float(np.average([x["d2"] for x in rows],weights=w)),"delta3":float(np.average([x["d3"] for x in rows],weights=w)),"ratio":float(np.median(np.concatenate(ratios))),"rgb_metrics":clean(pipe.get_average_eval_image_metrics()),"gaussian":gauss(pipe.model),"formal_training":False}
 a.out.mkdir(parents=True,exist_ok=True)
 with (a.out/"depth_metrics_per_frame.csv").open("w",newline="",encoding="utf-8") as stream:
  writer=csv.DictWriter(stream,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
 (a.out/"candidate_metrics.json").write_text(json.dumps(clean(summary),indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(clean(summary),sort_keys=True))
if __name__=="__main__": main()
