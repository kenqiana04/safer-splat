"""Restore PR33 C3 source from Git objects and build four static variants."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PREFIX = "reproduction/cross_dataset/tum_map_geometry_root_cause_repair_v1"
MODEL = "tum_metric_depth_splatfacto.py"
VARIANTS = ("E0_EXACT_C3_BASELINE", "E1_LATE_DEPTH_HOLD", "E2_REFINEMENT_LOCK_3000", "E3_LATE_DEPTH_HOLD_AND_LOCK")


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ast_sha(data: bytes) -> str:
    return sha(ast.dump(ast.parse(data.decode("utf-8")), annotate_fields=True, include_attributes=False).encode())


def patch_model(text: str, late: bool, lock: bool) -> str:
    marker = "    output_depth_during_training: bool = True\n"
    fields = ""
    if late:
        fields += "    late_depth_hold_start: int | None = 3000\n    late_depth_hold_lambda: float = 0.30\n"
    if lock:
        fields += "    refinement_lock_step: int | None = 3000\n"
    if fields:
        assert text.count(marker) == 1
        text = text.replace(marker, marker + fields)
    old = "        depth_loss, valid_ratio = metric_depth_huber_loss(prediction, target, accumulation, self.config.depth_loss_beta_m)\n        loss_dict[\"loss_depth_metric\"] = self.config.depth_loss_lambda * depth_loss\n"
    new = "        depth_loss, valid_ratio = metric_depth_huber_loss(prediction, target, accumulation, self.config.depth_loss_beta_m)\n        effective_lambda = self.config.depth_loss_lambda\n        if self.config.late_depth_hold_start is not None and int(self.step) >= self.config.late_depth_hold_start:\n            effective_lambda = self.config.late_depth_hold_lambda\n        loss_dict[\"loss_depth_metric\"] = effective_lambda * depth_loss\n" if late else old
    assert text.count(old) == 1
    text = text.replace(old, new)
    if lock:
        text += "\n    def step_post_backward(self, step: int):\n        if self.config.refinement_lock_step is not None and step >= self.config.refinement_lock_step:\n            return\n        return super().step_post_backward(step)\n"
    return text


def manifest(root: Path, commit: str, repo: Path) -> dict[str, object]:
    files=[]
    for path in sorted(root.rglob("*.py")):
        data=path.read_bytes(); rel=str(path.relative_to(root)).replace("\\", "/")
        original=f"{PREFIX}/{rel}"
        blob=None
        try: blob=git(repo,"rev-parse",f"{commit}:{original}").decode().strip()
        except subprocess.CalledProcessError: pass
        tree=ast.parse(data.decode("utf-8")); inventory=[node.name for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef))]
        files.append({"path":rel,"sha256":sha(data),"ast_sha256":ast_sha(data),"git_blob_sha":blob,"inventory":inventory})
    return {"source_commit":commit,"files":files,"manifest_sha256":sha(json.dumps(files,sort_keys=True).encode())}


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--commit",required=True); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    exact=args.out/"exact_pr33"; variants=args.out/"variants"; exact.mkdir(parents=True,exist_ok=False); variants.mkdir()
    paths=[x for x in git(args.repo,"ls-tree","-r","--name-only",args.commit,"--",PREFIX).decode().splitlines() if x.endswith(".py")]
    for original in paths:
        rel=Path(original).relative_to(PREFIX); target=exact/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(git(args.repo,"show",f"{args.commit}:{original}"))
    result={"exact_pr33":manifest(exact,args.commit,args.repo),"variants":{}}
    for name in VARIANTS:
        target=variants/name; shutil.copytree(exact,target); late=name in {"E1_LATE_DEPTH_HOLD","E3_LATE_DEPTH_HOLD_AND_LOCK"}; lock=name in {"E2_REFINEMENT_LOCK_3000","E3_LATE_DEPTH_HOLD_AND_LOCK"}
        if late or lock:
            model=target/MODEL; model.write_text(patch_model(model.read_text(encoding="utf-8"),late,lock),encoding="utf-8",newline="\n")
        result["variants"][name]=manifest(target,args.commit,args.repo)
    (args.out/"build_manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:v["manifest_sha256"] for k,v in result["variants"].items()},sort_keys=True))


if __name__ == "__main__": main()
