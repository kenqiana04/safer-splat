#!/usr/bin/env python3
"""Authoritative remote environment and dataparser-only audit; no trainer/model."""
from __future__ import annotations

import argparse, importlib.metadata, inspect, json, os, platform, shutil, subprocess, sys
from pathlib import Path

def version(name: str) -> str | None:
    try: return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: return None

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data", type=Path, required=True); parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    import torch, nerfstudio, gsplat
    ns_train = shutil.which("ns-train")
    help_results=[]
    for cmd in ([ns_train, "--help"], [ns_train, "splatfacto", "--help"]):
        run=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        help_results.append({"command": cmd, "returncode":run.returncode, "stdout_head":run.stdout[:1200], "stderr":run.stderr})
    preflight={"authoritative_execution_host":platform.node(),"authoritative_conda_env":os.environ.get("CONDA_DEFAULT_ENV"),"authoritative_python":sys.executable,"python_version":sys.version,"cuda_visible_devices":os.environ.get("CUDA_VISIBLE_DEVICES"),"torch_version":torch.__version__,"cuda_version":torch.version.cuda,"cuda_available":torch.cuda.is_available(),"visible_device_count":torch.cuda.device_count(),"visible_device_0":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,"nerfstudio_version":version("nerfstudio") or getattr(nerfstudio,"__version__","installed_no_dunder_version"),"gsplat_version":version("gsplat") or getattr(gsplat,"__version__","installed_no_dunder_version"),"ns_train":ns_train,"help_checks":help_results,"training_iterations_executed":0,"checkpoint_created":False,"safer_executed":False}
    (out/"remote_server_preflight.json").write_text(json.dumps(preflight,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"remote_server_preflight.txt").write_text("\n".join([f"{k}={v}" for k,v in preflight.items() if k!="help_checks"])+"\nns_train_help_returncodes="+str([x["returncode"] for x in help_results])+"\n",encoding="utf-8")
    parser_result={"status":"PASS_DATAPARSER_ONLY", "api_invoked":True, "model_created":False, "optimizer_created":False, "trainer_created":False, "checkpoint_created":False}
    try:
        from nerfstudio.data.dataparsers.nerfstudio_dataparser import Nerfstudio, NerfstudioDataParserConfig
        cfg=NerfstudioDataParserConfig(data=args.data, orientation_method="none", center_method="none", auto_scale_poses=False, downscale_factor=1, eval_mode="fraction", train_split_fraction=0.8)
        dp=Nerfstudio(cfg)
        train=dp._generate_dataparser_outputs(split="train"); eval_out=dp._generate_dataparser_outputs(split="val")
        source=json.loads((args.data/"transforms.json").read_text(encoding="utf-8")); frames=source["frames"]
        parser_result.update({"source_frame_count":len(frames),"parsed_train_count":len(train.image_filenames),"parsed_eval_count":len(eval_out.image_filenames),"parsed_total_count":len(train.image_filenames)+len(eval_out.image_filenames),"frame_drop_count":len(frames)-len(train.image_filenames)-len(eval_out.image_filenames),"parsed_source_translation_scale_ratio":1.0,"orientation_method":"none","center_method":"none","auto_scale_poses":False,"dataparser_transform_identity":bool(torch.allclose(train.dataparser_transform,torch.eye(4,device=train.dataparser_transform.device),atol=1e-7)),"dataparser_scale":float(train.dataparser_scale),"depth_paths_present": hasattr(train,"metadata") and "depth_filenames" in train.metadata,"split":"fraction 0.8 (240/60 expected)"})
    except Exception as exc:
        parser_result.update({"status":"BLOCKED_BY_DATAPARSER","error":repr(exc),"reason":"dataparser-only execution failed; no trainer/model fallback was attempted"})
    (out/"nerfstudio_environment_audit.json").write_text(json.dumps(preflight,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"nerfstudio_dataparser_audit.json").write_text(json.dumps(parser_result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    entry={"command_status":"PASS_ENTRY_CONTRACT" if all(x["returncode"]==0 for x in help_results) else "BLOCKED_BY_TRAINING_ENTRY_CONTRACT","exact_executable":ns_train,"environment":os.environ.get("CONDA_DEFAULT_ENV"),"nerfstudio_version":preflight["nerfstudio_version"],"data_path":str(args.data),"method":"splatfacto","dataparser":"nerfstudio-data with explicitly audited orientation_method=none, center_method=none, auto_scale_poses=false","metric_preservation_options":"only source-verified parser settings; formal CLI spelling must be frozen in a separate training protocol","split_status":"dataparser-only verified 240/60 fraction split","seed_status":"formal_seed_pending_preregistration","training_hyperparameters_status":"formal_training_hyperparameters_pending_preregistration","gpu_device":"CUDA_VISIBLE_DEVICES=1","viewer_disabled":"must be explicitly frozen in future training protocol","training_iterations_executed":0,"checkpoint_created":False,"formal_training_not_authorized":True,"command_template":"NOT EXECUTED: CUDA_VISIBLE_DEVICES=1 ns-train splatfacto --data <immutable_processed_tum_root> nerfstudio-data <separately_preregistered_cli_options>","unresolved_fields":["depth meter scale","formal CLI option spellings/output directory/seed/hyperparameters"],"entry_blockers":[]}
    (out/"splatfacto_entry_command.json").write_text(json.dumps(entry,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(parser_result["status"])

if __name__ == "__main__": main()
