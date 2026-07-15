#!/usr/bin/env python3
"""Record existing preprocessing and Replica-renderer dependencies without changes."""
import argparse,csv,importlib.util,platform,sys
from pathlib import Path
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);x=a.parse_args();x.out.mkdir(parents=True,exist_ok=True);mods=['torch','numpy','scipy','PIL','cv2','open3d','trimesh','nerfstudio','gsplat','habitat_sim'];rows=[]
 for m in mods:
  s=importlib.util.find_spec(m);rows.append({'module':m,'available':bool(s),'module_path':s.origin if s else '','required_for_tum':m in ['numpy','PIL'],'required_for_replica':m=='habitat_sim'})
 with (x.out/'preprocessing_environment.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (x.out/'renderer_environment_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['renderer','available','decision']);w.writeheader();w.writerow({'renderer':'habitat_sim','available':False,'decision':'blocked_by_renderer_environment'})
 print(platform.python_version())
if __name__=='__main__':main()
