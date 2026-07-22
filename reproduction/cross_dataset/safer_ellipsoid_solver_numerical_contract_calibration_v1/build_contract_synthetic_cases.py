"""Fixed geometry-defined registry including separate nonsmooth/edge cases."""
from __future__ import annotations
import json
from pathlib import Path
EDGE = {'SURFACE_BOUNDARY':8,'PROJECTION_NONUNIQUE':8,'SIGN_BOUNDARY':8,'AXIS_TIE':8,'NUMERIC_EXTREME':8}
def main():
 out={'pr41_synthetic_seed':20260722,'pr41_case_count':4096,'edge_seed':20260716,'edge_case_count':sum(EDGE.values()),'edge_classes':EDGE,'classification_rule':'Input geometry only: surface/sign level, repeated axes, medial-axis projection uniqueness, and numeric scale range. No gradient result was used.'}
 Path(__file__).with_name('synthetic_case_registry_summary.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
