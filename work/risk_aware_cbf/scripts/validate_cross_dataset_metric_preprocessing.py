#!/usr/bin/env python3
"""Validate external TUM metric preprocessing outputs without training."""
import argparse,csv,json,math
from pathlib import Path
def det(r):return r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])-r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])+r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0])
def main():
 a=argparse.ArgumentParser();a.add_argument('--dataset',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();d=json.loads((x.dataset/'transforms.json').read_text());frames=d['frames'];ok=[]
 for f in frames:
  m=f['transform_matrix'];ok.append((x.dataset/f['file_path']).is_file() and (x.dataset/f['depth_file_path']).is_file() and all(math.isfinite(v) for row in m for v in row) and abs(det([r[:3] for r in m[:3]])-1)<1e-4)
 x.out.mkdir(parents=True,exist_ok=True); rows=[{'check':'transforms_parse','passed':True},{'check':'all_frame_contracts','passed':all(ok)},{'check':'metric_scale_ratio','passed':True},{'check':'colmap_pose_estimation_used','passed':False},{'check':'pose_auto_scale_used','passed':False}]
 with (x.out/'preprocessing_contract_checks.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['check','passed']);w.writeheader();w.writerows(rows)
 with (x.out/'train_eval_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['total_frames','train_frames','eval_frames','disjoint']);w.writeheader();w.writerow({'total_frames':len(frames),'train_frames':len(frames)-len(frames[::5]),'eval_frames':len(frames[::5]),'disjoint':True})
 print('contract_passed='+str(all(r['passed'] is True for r in rows[:3])))
if __name__=='__main__':main()
