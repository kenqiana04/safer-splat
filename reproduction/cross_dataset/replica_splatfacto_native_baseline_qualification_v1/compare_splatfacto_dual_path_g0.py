#!/usr/bin/env python3
"""Compare the two static G0 paths under the frozen numerical tolerances."""
from __future__ import annotations

import numpy as np

from _common import ROOT, atomic_json, load_json, update_stage


def main():
    native=load_json(ROOT/"safer_g0"/"splatfacto_safer_native_g0_summary.json"); canonical=load_json(ROOT/"safer_g0"/"splatfacto_safer_canonical_g0_summary.json"); destination=ROOT/"safer_g0"/"splatfacto_dual_path_g0_consistency.json"
    if not native.get("status","").endswith("PASS") or not canonical.get("status","").endswith("PASS"):
        atomic_json(destination,{"status":"NOT_AUTHORIZED_DUE_TO_G0_PATH_FAILURE"});return
    a=np.load(native["raw_static_result"]);b=np.load(canonical["raw_static_result"])
    checks={"h":bool(np.allclose(a["h"],b["h"],atol=1e-6,rtol=1e-5)),"gradient":bool(np.allclose(a["gradient"],b["gradient"],atol=1e-5,rtol=1e-4)),"hessian":bool(np.allclose(a["hessian"],b["hessian"],atol=1e-5,rtol=1e-4)),"query_identity":bool(np.array_equal(a["queries"],b["queries"]))}
    out={"status":"SPLATFACTO_DUAL_PATH_G0_CONSISTENCY_PASS" if all(checks.values()) else "SPLATFACTO_DUAL_PATH_G0_CONSISTENCY_FAILURE","checks":checks,"max_abs_difference":{"h":float(np.max(np.abs(a["h"]-b["h"]))),"gradient":float(np.max(np.abs(a["gradient"]-b["gradient"]))),"hessian":float(np.max(np.abs(a["hessian"]-b["hessian"])))} ,"active_index_cross_path_comparison_required":False}
    atomic_json(destination,out);update_stage("DUAL_PATH_CONSISTENCY","TERMINAL_SCIENTIFIC_RESULT" if all(checks.values()) else "FAILED_INFRASTRUCTURE",result_status=out["status"]);print(out["status"])


if __name__=="__main__": main()
