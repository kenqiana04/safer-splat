#!/usr/bin/env python3
"""Materialize final local artifacts from authoritative 4090 remote evidence."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; REMOTE=ROOT/"remote_outputs"
def read(name): return json.loads((REMOTE/name).read_text(encoding="utf-8"))
for name in ["input_asset_inventory.csv","rgb_integrity.csv","depth_integrity.csv","rgb_depth_pairing_audit.csv","transforms_contract_audit.json","pose_geometry_audit.csv","metric_scale_audit.json","nerfstudio_environment_audit.json","nerfstudio_dataparser_audit.json","splatfacto_entry_command.json"]:
    shutil.copy2(REMOTE/name,ROOT/name)
pre=read("remote_server_preflight.json"); transforms=read("transforms_contract_audit.json"); pair=read("pairing_summary.json"); rgb=read("rgb_integrity_summary.json"); depth=read("depth_integrity_summary.json"); scale=read("depth_scale_contract.json"); parser=read("nerfstudio_dataparser_audit.json"); source_hash=read("source_asset_hash_manifest.json")
identity=read("../dataset_identity.json") if False else json.loads((ROOT/"dataset_identity.json").read_text(encoding="utf-8"))
identity.update({"authoritative_execution_host":"zlab-Super-Server","authoritative_asset_root":"/disk1/zlab/cross_dataset_assets","processed_transforms_path":transforms["processed_transforms_path"],"processed_transforms_sha256":transforms["sha256"],"selected_frame_count":300})
(ROOT/"dataset_identity.json").write_text(json.dumps(identity,indent=2,sort_keys=True)+"\n",encoding="utf-8")
env={"authoritative_execution_host":"zlab-Super-Server","authoritative_conda_env":"safer_splat_official","authoritative_python":pre["authoritative_python"],"authoritative_gpu":pre["visible_device_0"],"windows_probe_role":"superseded_non_authoritative_local_probe","used_for_gate_decision":False,"remote_execution_complete":True,"remote_asset_root":"/disk1/zlab/cross_dataset_assets","remote_sequence_root":"/disk1/zlab/cross_dataset_assets/raw/tum_rgbd/rgbd_dataset_freiburg1_room","remote_processed_transforms_path":transforms["processed_transforms_path"]}
(ROOT/"environment_provenance.json").write_text(json.dumps(env,indent=2,sort_keys=True)+"\n",encoding="utf-8")
remote_manifest={"remote_host":"zlab-Super-Server","remote_tmp":"/tmp/tum_g0_checkpoint_entry_audit_v1_zlab/outputs","files":{str(p.relative_to(REMOTE)).replace("\\\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(REMOTE.iterdir()) if p.is_file()}}
(ROOT/"remote_output_manifest.json").write_text(json.dumps(remote_manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
decision={"decision":"BLOCKED_BY_CRITICAL_PROVENANCE","additional_blockers":["BLOCKED_BY_DATAPARSER"],"authoritative_execution_host":"zlab-Super-Server","data_and_checkpoint_entry_substage":"blocked","safer_navigation_substage":"not_started","global_G0_status":"blocked","formal_checkpoint_exists":False,"safer_loader_validated":False,"G1_allowed":False,"training_iterations_executed":0,"checkpoint_created":False,"reason":"Remote RGB/depth/pose structural audit passed, but frozen evidence does not establish depth meter scale and dataparser-only execution raises a shape error without any model/trainer fallback."}
(ROOT/"checkpoint_entry_decision.json").write_text(json.dumps(decision,indent=2,sort_keys=True)+"\n",encoding="utf-8")
registry=json.loads((ROOT/"G0_GATE_REGISTRY.json").read_text(encoding="utf-8"))
statuses={"G0-A":"passed","G0-B":"passed","G0-C":"passed","G0-D":"blocked_by_critical_provenance","G0-E":"passed","G0-F":"passed","G0-G":"passed","G0-H":"blocked_by_critical_provenance","G0-I":"blocked_by_dataparser","G0-J":"passed_entry_contract_only","G0-K":"adapter_likely_required_static_only","G0-L":"passed"}
for gate in registry["gates"]: gate["status"]=statuses[gate["id"]]
registry["final_decision"]=decision["decision"]
(ROOT/"G0_GATE_REGISTRY.json").write_text(json.dumps(registry,indent=2,sort_keys=True)+"\n",encoding="utf-8")
report=f'''# REPORT: TUM Remaining G0 Checkpoint-Entry Audit V1

## Executive Summary

The authoritative audit ran on `zlab-Super-Server` (4090) against the immutable
TUM root `/disk1/zlab/cross_dataset_assets`. The exact sequence is
`rgbd_dataset_freiburg1_room` (`TUM_FR1_ROOM`). The frozen transforms file is
`{transforms["processed_transforms_path"]}` and its SHA-256 matches the frozen
value: `{transforms["sha256"]}`. All 300 selected RGB, depth, and pose records
were read on the server; structural integrity, pairing, rigid-pose checks, and
source pre/post hashes passed. The formal decision is
**`BLOCKED_BY_CRITICAL_PROVENANCE`**, with additional
**`BLOCKED_BY_DATAPARSER`** evidence. No training, checkpoint, SAFER loader,
baseline, navigation, or G1 execution occurred.

## Execution Environment Correction

Stage 0 preregistration was committed in the Windows Git workspace. Windows is
orchestration-only; its preliminary local probe was superseded and was not used
for any gate. Data, CUDA, Nerfstudio, gsplat, PyTorch, and dataparser evidence
comes only from the 4090 server: conda `safer_splat_official`, Python
`{pre["python_version"]}`, PyTorch `{pre["torch_version"]}`, CUDA
`{pre["cuda_version"]}`, Nerfstudio `{pre["nerfstudio_version"]}`, gsplat
`{pre["gsplat_version"]}`, and visible GPU `{pre["visible_device_0"]}`.

## Data and Geometry Results

- Remote raw root: `/disk1/zlab/cross_dataset_assets/raw/tum_rgbd/rgbd_dataset_freiburg1_room`
- Processed frames: 300 RGB, 300 depth, 300 poses.
- RGB: `{rgb["status"]}`; all-zero `{rgb["all_zero_count"]}`, duplicate `{rgb["duplicate_count"]}`.
- Depth: `{depth["status"]}`; all-zero `{depth["all_zero_count"]}`, nonfinite `{depth["nonfinite_count"]}`.
- Pairing: `{pair["status"]}`, no reassociation; maximum historical RGB-depth offset `{pair["max_rgb_depth_offset_s"]}` s.
- Pose/intrinsics/transforms: required fields present and preregistered rigid tolerances audited from the server file.
- Source raw metadata hashes were unchanged before/after audit: `{source_hash["unchanged"]}`.

## Metric Scale and Dataparser

Depth scale is not guessed: the frozen preprocessor copies depth PNGs and the
frozen transforms omit `depth_unit_scale_factor`. Consequently the raw unit and
meter conversion are not source-established (`{scale["status"]}`).

The server-only dataparser API audit used `orientation_method=none`,
`center_method=none`, and `auto_scale_poses=false`, without model, optimizer,
trainer, viewer, or checkpoint. It raised `{parser.get("error")}`. No fallback
to `ns-train` or training was attempted, so frame-drop and parsed/source
translation-ratio are unresolved.

## Splatfacto and SAFER Boundary

`ns-train --help` and `ns-train splatfacto --help` returned zero on the server.
The command artifact is a non-executed contract only; formal split/seed/output
settings and all training hyperparameters remain pending separate preregistration.
`training_iterations_executed=0` and `checkpoint_created=false`.

The SAFER review is `static_source_contract_only`: expected attributes are means,
scales, quaternion rotations, opacities, and colors/SH. Its result is not a
loader pass and cannot validate a nonexistent TUM checkpoint.

## Gate Decision and Next Step

Data structural gates are supported by the 4090 evidence, but global G0 remains
`blocked`; `formal_checkpoint_exists=false`, `safer_loader_validated=false`, and
`G1_allowed=false`. Formal TUM Splatfacto Training Protocol Preregistration is
not yet authorized. The next task must first establish a source-backed depth
unit/scale contract and resolve the dataparser shape failure without training.
G1 SAFER baseline remains forbidden.
'''
(ROOT/"REPORT_TUM_REMAINING_G0_CHECKPOINT_ENTRY_V1.md").write_text(report,encoding="utf-8")
excluded={"audit_bundle_sha256.json","validation_result.json"}; files={}
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts:
        files[str(path.relative_to(ROOT)).replace("\\\\","/")]=hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT/"audit_bundle_sha256.json").write_text(json.dumps({"status":"complete_remote_authoritative_blocked_audit","files":files,"excluded":sorted(excluded)},indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(decision["decision"])
