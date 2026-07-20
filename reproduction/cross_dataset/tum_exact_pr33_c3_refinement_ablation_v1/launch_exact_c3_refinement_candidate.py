"""Launch a static PR33-source candidate without modifying its source tree."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
from nerfstudio.engine.trainer import Trainer

def load(root: Path):
    sys.path.insert(0,str(root)); spec=importlib.util.spec_from_file_location("exact_launcher",root/"launch_nonformal_repair_candidate.py"); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,required=True); ap.add_argument("--output-root",type=Path,required=True); ap.add_argument("--steps",type=int,choices=(100,6000,10000),required=True); ap.add_argument("--candidate",default="C3_METRIC_SEED_PLUS_DEPTH"); args=ap.parse_args()
    if any(args.output_root.iterdir()) if args.output_root.exists() else False: raise SystemExit("output root must be empty")
    args.output_root.mkdir(parents=True,exist_ok=True); cfg=load(args.source_root).configure(args.candidate,args.output_root,args.steps)
    trainer=Trainer(cfg,local_rank=0,world_size=1); trainer.setup(test_mode="val"); trainer.train(); print(json.dumps({"candidate":args.candidate,"steps":args.steps,"output_root":str(args.output_root),"formal_training":False},sort_keys=True))
if __name__ == "__main__": main()
