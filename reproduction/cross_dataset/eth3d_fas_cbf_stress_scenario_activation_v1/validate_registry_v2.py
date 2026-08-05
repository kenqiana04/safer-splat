#!/usr/bin/env python3
"""Fail-closed registry validation and activation-quota gate."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from task_config_v2 import *  # noqa: F403

def main() -> int:
 p=argparse.ArgumentParser(); p.add_argument("--registry",type=Path,required=True); a=p.parse_args(); r=json.loads(a.registry.read_text()); s=r["scenarios"]
 counts=Counter(x["group"] for x in s); ids=[x["scenario_id"] for x in s]; candidates=[x["candidate_id"] for x in s]
 q={
  "G0_H1":sum(x["shadow_stage_reachability"]["S1"]["projection_attempted"] for x in s if x["group"]==GROUPS[0]),
  "G0_H3":sum(x["shadow_stage_reachability"].get("S3",{}).get("verifier_trigger",False) for x in s if x["group"]==GROUPS[0]),
  "G0_H4":sum(x["shadow_stage_reachability"].get("S4",{}).get("recovery_trigger",False) for x in s if x["group"]==GROUPS[0]),
  "G1_H1":sum(x["shadow_stage_reachability"]["S1"]["projection_attempted"] for x in s if x["group"]==GROUPS[1]),
  "G1_projection_success":sum(x["shadow_stage_reachability"]["S1"]["projection_success"] for x in s if x["group"]==GROUPS[1]),
  "G2_H2":sum(x["shadow_stage_reachability"]["S2"]["H2_DOMINANCE_ACTIVE"] for x in s if x["group"]==GROUPS[2]),
  "G3_H3":sum(x["shadow_stage_reachability"]["S3"]["verifier_trigger"] for x in s if x["group"]==GROUPS[3]),
  "G3_unavoidable":sum(x["shadow_stage_reachability"]["S3"]["unavoidable_immediate_segment"] for x in s if x["group"]==GROUPS[3]),
  "G4_H4":sum(x["shadow_stage_reachability"]["S4"]["recovery_trigger"] for x in s if x["group"]==GROUPS[4]),
  "G4_recoverable":sum(x["shadow_stage_reachability"]["S4"]["recovery_recoverable"] for x in s if x["group"]==GROUPS[4])}
 gates={"count":len(s)==100,"groups":counts==Counter({g:20 for g in GROUPS}),"unique_ids":len(set(ids))==100,"unique_states":len(set(candidates))==100,
  "logical_sha":r["registry_sha256"]==sha256_json({k:v for k,v in r.items() if k not in {"registry_sha256","status"}}),
  "G0":q["G0_H1"]<=2 and q["G0_H3"]<=2 and q["G0_H4"]<=2,"G1":q["G1_H1"]>=16 and q["G1_projection_success"]>=12,
  "G2":q["G2_H2"]>=16,"G3":q["G3_H3"]>=16 and q["G3_unavoidable"]<=4,"G4":q["G4_H4"]>=16 and q["G4_recoverable"]>=12,
  "no_formal_metrics":all(x.get("formal_rollout_metric_read_count")==0 for x in s),"method_shared":r["method_independent"]}
 result={"status":"PASS_V2_REGISTRY_VALIDATION" if all(gates.values()) else "V2_REGISTRY_VALIDATION_FAILED","gates":gates,"activation_quotas":q,"counts":dict(counts),"raw_sha256":sha256_file(a.registry),"logical_sha256":r["registry_sha256"]}
 atomic_json(a.registry.parent/"registry_validation.json",result); print(json.dumps(result,sort_keys=True))
 if not all(gates.values()): raise RuntimeError(result)
 return 0
if __name__=="__main__": raise SystemExit(main())
