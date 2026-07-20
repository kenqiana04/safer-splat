"""Enforce the exact PR33/minimal-diff source contract."""
from __future__ import annotations
import argparse, ast, difflib, hashlib, json
from pathlib import Path

def normalized(text: str) -> str: return ast.dump(ast.parse(text),annotate_fields=True,include_attributes=False)
def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def changed(a: Path,b: Path) -> list[str]:
    return [str(x.relative_to(a)).replace("\\","/") for x in sorted(a.rglob("*.py")) if x.read_bytes() != (b/x.relative_to(a)).read_bytes()]
def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--exact",type=Path,required=True); ap.add_argument("--variants",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    result={"status":"PASS_MINIMAL_DIFF_CANDIDATE_SOURCE_GATE","variants":{}}
    for name in ("E0_EXACT_C3_BASELINE","E1_LATE_DEPTH_HOLD","E2_REFINEMENT_LOCK_3000","E3_LATE_DEPTH_HOLD_AND_LOCK"):
        root=args.variants/name; diffs=changed(args.exact,root); detail={"changed_files":diffs,"source_sha256":sha(b"".join(p.read_bytes() for p in sorted(root.rglob("*.py"))))}
        if name=="E0_EXACT_C3_BASELINE": assert not diffs, diffs
        else:
            assert diffs==["tum_metric_depth_splatfacto.py"], diffs
            text=(root/"tum_metric_depth_splatfacto.py").read_text(encoding="utf-8")
            assert "TumMetricDepthSplatfactoModel" in text and "class TumMetricDepthSplatfactoModel(SplatfactoModel)" in text
            assert "instrumentation" not in text and "quantile" not in text and ".cpu()" not in text
            if "E1" in name or "E3" in name: assert "late_depth_hold_lambda: float = 0.30" in text and "effective_lambda * depth_loss" in text
            if "E2" in name or "E3" in name: assert "refinement_lock_step: int | None = 3000" in text and "def step_post_backward" in text
        detail["model_ast_sha256"]=sha(normalized((root/"tum_metric_depth_splatfacto.py").read_text(encoding="utf-8")).encode()); result["variants"][name]=detail
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
