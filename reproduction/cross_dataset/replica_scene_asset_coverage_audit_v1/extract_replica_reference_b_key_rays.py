#!/usr/bin/env python3
"""Extract the four frozen center rays reserved for brute-force Reference B."""
from __future__ import annotations
import csv
from _common import ROOT

def main() -> None:
    src=ROOT/"independent_raycast/rays.csv";dst=ROOT/"independent_raycast/reference_b_key_rays.csv"
    with src.open(encoding="utf-8",newline="") as a,dst.open("w",encoding="utf-8",newline="") as b:
        r=csv.DictReader(a);w=csv.DictWriter(b,fieldnames=r.fieldnames);w.writeheader()
        rows=[x for x in r if x["reference_b_key"]=="true"]
        if len(rows)!=4:raise SystemExit("unexpected_reference_b_key_count")
        w.writerows(rows)

if __name__=="__main__":main()
