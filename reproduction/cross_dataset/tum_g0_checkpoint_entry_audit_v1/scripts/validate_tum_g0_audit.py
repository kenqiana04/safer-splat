#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE="0fb8698e8590aead60032487fc3321c07f2fd99c"
def load(name): return json.loads((ROOT/name).read_text(encoding="utf-8"))
pre=load("remote_outputs/remote_server_preflight.json"); trans=load("transforms_contract_audit.json"); src=load("remote_outputs/source_asset_hash_manifest.json"); decision=load("checkpoint_entry_decision.json"); bundle=load("audit_bundle_sha256.json")
checks=[
 ("authoritative_host",pre.get("authoritative_execution_host")=="zlab-Super-Server"),("authoritative_env",pre.get("authoritative_conda_env")=="/disk1/zlab/conda_envs/safer_splat_official"),("remote_asset_root",(ROOT/"remote_outputs/input_asset_inventory.csv").is_file()),("sequence",load("dataset_identity.json").get("sequence_name")=="rgbd_dataset_freiburg1_room"),("transforms_hash",trans.get("hash_matches") is True),("remote_rgb_depth_pose",src.get("selected_rgb_count")==300 and src.get("selected_depth_count")==300 and src.get("selected_pose_count")==300),("source_unchanged",src.get("unchanged") is True),("windows_probe_excluded",load("environment_provenance.json").get("windows_probe_role")=="superseded_non_authoritative_local_probe"),("no_training",pre.get("training_iterations_executed")==0 and pre.get("checkpoint_created") is False),("blocked_not_promoted",decision.get("decision")=="BLOCKED_BY_CRITICAL_PROVENANCE" and decision.get("G1_allowed") is False)]
manifest=load("remote_output_manifest.json"); checks.append(("remote_output_hashes",all(hashlib.sha256((ROOT/"remote_outputs"/k).read_bytes()).hexdigest()==v for k,v in manifest["files"].items())))
for rel in ["reproduction/experiment_protocol_freeze_v1","cbf","splat","ellipsoids","dynamics","run.py"]: checks.append(("zero_diff:"+rel,subprocess.run(["git","diff","--exit-code",BASE,"--",rel]).returncode==0))
bundle_ok=all((ROOT/k).is_file() and hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in bundle["files"].items()); checks.append(("bundle_hashes",bundle_ok))
status="BLOCKED_BY_CRITICAL_PROVENANCE" if all(v for _,v in checks) else "FAIL"
(ROOT/"validation_result.json").write_text(json.dumps({"status":status,"checks":[{"check":k,"passed":v} for k,v in checks],"authoritative_data_host":"zlab-Super-Server","authoritative_runtime_host":"zlab-Super-Server","authoritative_conda_env":"safer_splat_official","authoritative_python":pre["authoritative_python"],"authoritative_gpu":pre["visible_device_0"],"remote_execution_complete":True,"training_iterations_executed":0,"checkpoint_created":False,"windows_probe_role":"superseded_non_authoritative_local_probe"},indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(status); raise SystemExit(0 if status!="FAIL" else 1)
