"""Launch exactly one fresh task-owned nonformal tuned-surface candidate."""
from __future__ import annotations
import argparse, importlib.util, json, shutil, sys
from pathlib import Path
from nerfstudio.engine.trainer import Trainer

NAMES={"S0_TUNED_BASELINE":(False,False),"S1_SURFACE_ORIENTED_PRIOR":(True,False),"S2_POINT_TO_PLANE_LOSS":(False,True),"S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE":(True,True)}
def load(root: Path):
    sys.path.insert(0,str(root)); spec=importlib.util.spec_from_file_location("tuned_surface_launcher",root/"launch_nonformal_repair_candidate.py"); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module
def configure(source: Path, candidate: str, output: Path, steps: int, prior: Path, targets: Path):
    use_prior,use_loss=NAMES[candidate]; module=load(source); config=module.configure("C3_METRIC_SEED_PLUS_DEPTH",output,steps); model=config.pipeline.model
    model.depth_loss_lambda=.10; model.depth_loss_beta_m=.20; model.depth_unit_scale_factor=.0002; model.depth_accumulation_threshold=1e-4; model.late_depth_hold_start=3000; model.late_depth_hold_lambda=.50; model.refinement_lock_step=2000
    if use_prior: model.surface_prior_path=prior
    if use_loss: model.surface_target_root=targets; model.surface_loss_lambda=.10; model.surface_loss_beta_m=.02
    config.machine.seed=20260716; config.max_num_iterations=steps; config.steps_per_save=steps; config.steps_per_eval_all_images=steps; config.steps_per_eval_image=steps; config.experiment_name=f"NONFORMAL_TUNED_SURFACE_{candidate}"; config.timestamp=f"seed20260716_{steps:05d}"; config.load_dir=None; config.load_checkpoint=None; config.load_step=None
    return config
def contract(config,candidate,source,output,prior,targets):
    m=config.pipeline.model; return {"candidate":candidate,"source_root":str(source),"output_root":str(output),"steps":int(config.max_num_iterations),"seed":int(config.machine.seed),"late_depth_hold_start":int(m.late_depth_hold_start),"late_depth_hold_lambda":float(m.late_depth_hold_lambda),"refinement_lock_step":int(m.refinement_lock_step),"depth_loss_beta_m":float(m.depth_loss_beta_m),"depth_loss_lambda":float(m.depth_loss_lambda),"surface_prior":str(prior) if NAMES[candidate][0] else None,"surface_targets":str(targets) if NAMES[candidate][1] else None,"surface_loss_lambda":float(m.surface_loss_lambda) if NAMES[candidate][1] else None,"surface_loss_beta_m":float(m.surface_loss_beta_m) if NAMES[candidate][1] else None,"load_dir":None,"load_checkpoint":None,"load_step":None,"formal_training":False,"resume":False}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--source",type=Path,required=True); p.add_argument("--candidate",choices=NAMES,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--steps",type=int,choices=(100,6000,10000),required=True); p.add_argument("--prior",type=Path,required=True); p.add_argument("--targets",type=Path,required=True); p.add_argument("--contract",type=Path,required=True); a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()): raise RuntimeError(f"OUTPUT_NOT_EMPTY:{a.output}")
    a.output.mkdir(parents=True,exist_ok=True); config=configure(a.source,a.candidate,a.output,a.steps,a.prior,a.targets); info=contract(config,a.candidate,a.source,a.output,a.prior,a.targets); a.contract.write_text(json.dumps(info,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    trainer=Trainer(config,local_rank=0,world_size=1); trainer.setup(test_mode="val"); trainer.train(); print(json.dumps(info,sort_keys=True))
if __name__=="__main__": main()
