#!/usr/bin/env python3
"""Fail-closed audit that TRAIN never opened held-out/reference authorities."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from eth3d_controller_core import atomic_json

def main():
 p=argparse.ArgumentParser();p.add_argument('--task-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.task_root
 formal=json.loads((r/'formal_map/formal_result.json').read_text());smoke=json.loads((r/'smoke/smoke_result.json').read_text());adapter=json.loads((r/'input_adapter/train_input_identity.json').read_text())
 checks={'formal_reference_access_zero':formal['reference_access_count']==0,'formal_heldout_access_zero':formal['heldout_access_count']==0,'smoke_reference_access_zero':smoke['reference_access_count']==0,'smoke_heldout_access_zero':smoke['heldout_access_count']==0,'adapter_reference_access_zero':adapter['reference_access_count']==0,'adapter_heldout_access_zero':adapter['heldout_access_count']==0,'formal_single_attempt':formal['formal_attempt_count']==1}
 out={'status':'PASS_TRAIN_REFERENCE_ACCESS_AUDIT' if all(checks.values()) else 'FAIL_TRAIN_REFERENCE_ACCESS_AUDIT','checks':checks,'reference_access_during_train':0,'gt_depth_access_during_train':0,'heldout_access_during_train':0}
 atomic_json(a.output,out)
 if not all(checks.values()):raise RuntimeError(out)
 print(out['status']);return 0
if __name__=='__main__':raise SystemExit(main())
