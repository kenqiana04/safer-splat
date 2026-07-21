"""Reject variant changes outside the registered prior and point-to-plane hooks."""
from __future__ import annotations
import argparse, ast, hashlib, json
from pathlib import Path

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def ast_sha(path: Path) -> str: return hashlib.sha256(ast.dump(ast.parse(path.read_text(encoding="utf-8")),include_attributes=False).encode()).hexdigest()
def files(root: Path) -> dict[str,str]: return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob("*.py"))}
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--baseline",type=Path,required=True); p.add_argument("--variants",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); base=files(a.baseline); out={"variants":{},"status":"PASS_TUNED_SURFACE_MINIMAL_DIFF_SOURCE_GATE"}
    contracts={"S0_TUNED_BASELINE":(),"S1_SURFACE_ORIENTED_PRIOR":("surface_prior_path","populate_modules"),"S2_POINT_TO_PLANE_LOSS":("surface_target_root","loss_surface_point_to_plane","surface_loss_lambda","surface_loss_beta_m"),"S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE":("surface_prior_path","surface_target_root","loss_surface_point_to_plane")}
    forbidden=("depth_loss_lambda = 0.","depth_loss_beta_m = 0.","late_depth_hold_lambda =","refinement_lock_step =","step_post_backward", "Trainer.setup")
    for name,required in contracts.items():
        root=a.variants/name; current=files(root); changed=sorted(k for k in set(base)|set(current) if base.get(k)!=current.get(k)); text=(root/"tum_metric_depth_splatfacto.py").read_text(encoding="utf-8"); detail={"changed_files":changed,"model_ast_sha256":ast_sha(root/"tum_metric_depth_splatfacto.py"),"required_present":all(token in text for token in required),"forbidden_change":False}
        if name=="S0_TUNED_BASELINE": detail["semantic_diff_count"]=len(changed); detail["pass"]=not changed
        else:
            detail["forbidden_change"]=any(token in text and token not in (a.baseline/"tum_metric_depth_splatfacto.py").read_text(encoding="utf-8") for token in forbidden); detail["pass"]=(changed==["tum_metric_depth_splatfacto.py"] and detail["required_present"] and not detail["forbidden_change"])
        out["variants"][name]=detail
    if not all(v["pass"] for v in out["variants"].values()): out["status"]="BLOCKED_BY_TUNED_SURFACE_MINIMAL_DIFF_GATE"
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
