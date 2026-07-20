import argparse,csv,json,sys,time
from pathlib import Path
import numpy as np, torch, imageio.v3 as iio
sys.path.insert(0,'/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/local_method')
from launch_nonformal_repair_candidate import configure

def metric(gt,pred):
    m=(gt>0)&np.isfinite(gt)&np.isfinite(pred)&(pred>0)
    g,p=gt[m],pred[m]
    if not m.any(): return dict(overlap=0,absrel=float('nan'),sqrel=float('nan'),rmse=float('nan'),rmse_log=float('nan'),d1=float('nan'),d2=float('nan'),d3=float('nan'),ratio=np.array([],np.float32))
    r=p/g; th=np.maximum(r,1/r)
    return dict(overlap=int(m.sum()),absrel=float(np.mean(np.abs(p-g)/g)),sqrel=float(np.mean((p-g)**2/g)),rmse=float(np.sqrt(np.mean((p-g)**2))),rmse_log=float(np.sqrt(np.mean((np.log(p)-np.log(g))**2))),d1=float(np.mean(th<1.25)),d2=float(np.mean(th<1.25**2)),d3=float(np.mean(th<1.25**3)),ratio=r.astype(np.float32))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate',required=True); ap.add_argument('--checkpoint',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    cfg=configure(args.candidate,args.out/'ephemeral_eval_config',3000); cfg.load_dir=None; cfg.load_checkpoint=None; cfg.load_step=None
    pipe=cfg.pipeline.setup(device='cuda:0',test_mode='test',world_size=1,local_rank=0)
    ckpt=torch.load(args.checkpoint,map_location='cpu'); pipe.load_state_dict(ckpt['pipeline'],strict=True); pipe.eval()
    outputs=pipe.datamanager.eval_dataset._dataparser_outputs; files=outputs.metadata['depth_filenames']; rows=[]; ratios=[]
    with torch.no_grad():
      for i in range(len(pipe.datamanager.fixed_indices_eval_dataloader)):
        cam,batch=pipe.datamanager.fixed_indices_eval_dataloader[i]
        cam=cam.to(pipe.device); out=pipe.model.get_outputs_for_camera(cam)
        pred=out['depth'].squeeze(-1).detach().float().cpu().numpy(); gt=iio.imread(files[int(batch['image_idx'])]).astype(np.float32)*.0002
        z=metric(gt,pred); rows.append(dict(eval_index=i,image_idx=int(batch['image_idx']),depth_path=str(files[int(batch['image_idx'])]),valid_gt=int((gt>0).sum()),**{k:v for k,v in z.items() if k!='ratio'}));ratios.append(z['ratio'])
    weights=np.array([r['overlap'] for r in rows]); ar=np.concatenate(ratios)
    s=dict(candidate=args.candidate,checkpoint=str(args.checkpoint),checkpoint_step=int(ckpt['step']),frame_count=len(rows),depth_semantic='expected_depth_from_splatfacto_RGB+ED; raw metric comparison; no scale alignment',valid_overlap_pixel_count=int(weights.sum()),valid_overlap_ratio=float(weights.sum()/sum(r['valid_gt'] for r in rows)),AbsRel=float(np.average([r['absrel'] for r in rows],weights=weights)),SqRel=float(np.average([r['sqrel'] for r in rows],weights=weights)),RMSE=float(np.sqrt(np.average(np.square([r['rmse'] for r in rows]),weights=weights)),),RMSE_log=float(np.sqrt(np.average(np.square([r['rmse_log'] for r in rows]),weights=weights)),),delta_1_25=float(np.average([r['d1'] for r in rows],weights=weights)),delta_1_25_sq=float(np.average([r['d2'] for r in rows],weights=weights)),delta_1_25_cu=float(np.average([r['d3'] for r in rows],weights=weights)),median_predicted_over_gt_depth_ratio=float(np.median(ar)),seed=20260716,formal_training=False)
    with (args.out/'depth_metrics_per_frame.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    (args.out/'depth_metrics_raw.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n');print(json.dumps(s,sort_keys=True))
if __name__=='__main__': main()
