#!/usr/bin/env python3
"""Produce one decomposed overall asset classification, never the old broad label."""
from __future__ import annotations
from _common import ROOT, atomic_json, load_json

def main()->None:
    joint=load_json(ROOT/"joint_failure_analysis/replica_joint_failure_mechanism.json")
    rgb=load_json(ROOT/"rgb_only_analysis/replica_rgb_only_frame_0034_audit.json")
    overall="PURE_GEOMETRY_COVERAGE_DEFECT" if joint["JOINT_32_PRIMARY_MECHANISM"]=="ASSET_GEOMETRY_COVERAGE_GAPS_AT_FROZEN_FRUSTA" and rgb["RGB_ONLY_FRAME_0034_MECHANISM"]=="RGB_ONLY_LEGITIMATELY_DARK_VIEW_UNDER_V1_THRESHOLD" else "ASSET_CAUSE_REMAINS_UNRESOLVED"
    atomic_json(ROOT/"classification/replica_asset_failure_classification.json",{"status":"PASS_DECOMPOSED_ASSET_CLASSIFICATION" if overall!="ASSET_CAUSE_REMAINS_UNRESOLVED" else "UNRESOLVED","JOINT_32_PRIMARY_MECHANISM":joint["JOINT_32_PRIMARY_MECHANISM"],"RGB_ONLY_FRAME_0034_MECHANISM":rgb["RGB_ONLY_FRAME_0034_MECHANISM"],"OVERALL_ASSET_AUDIT_CLASSIFICATION":overall,"deprecated_broad_label_not_used":True})

if __name__=="__main__":main()
