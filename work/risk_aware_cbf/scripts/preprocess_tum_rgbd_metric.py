#!/usr/bin/env python3
"""Build a deterministic metric Nerfstudio-compatible TUM RGB-D dataset externally."""
from __future__ import annotations
import argparse, csv, json, math, shutil
from pathlib import Path

def rows(path):
 out=[]
 for line in path.read_text().splitlines():
  if line and not line.startswith('#'):
   p=line.split(); out.append((float(p[0]),p[1:]))
 return out
def near(items,t): return min(items,key=lambda x:abs(x[0]-t))
def mat(q,t):
 x,y,z,w=map(float,q); n=x*x+y*y+z*z+w*w; x,y,z,w=x/math.sqrt(n),y/math.sqrt(n),z/math.sqrt(n),w/math.sqrt(n)
 return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),float(t[0])],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),float(t[1])],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),float(t[2])],[0,0,0,1]]
def main():
 a=argparse.ArgumentParser();a.add_argument('--raw',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--result-dir',type=Path,required=True);x=a.parse_args(); raw=x.raw; out=x.out; out.mkdir(parents=True,exist_ok=True); (out/'images').mkdir(exist_ok=True);(out/'depth').mkdir(exist_ok=True)
 rgb,dep,pose=rows(raw/'rgb.txt'),rows(raw/'depth.txt'),rows(raw/'groundtruth.txt'); triples=[]
 for t,p in rgb:
  d,g=near(dep,t),near(pose,t)
  if abs(d[0]-t)<=.02 and abs(g[0]-t)<=.02: triples.append((t,p[0],d[1][0],g[1]))
 n=len(triples); idx=sorted(set(round(i*(n-1)/(min(300,n)-1)) for i in range(min(300,n)))) if n>1 else [0]; frames=[]; assoc=[]
 for j,i in enumerate(idx):
  t,r,d,g=triples[i]; rp,dp=raw/r,raw/d; rn=f'{j:04d}.png'; shutil.copy2(rp,out/'images'/rn);shutil.copy2(dp,out/'depth'/rn); frames.append({'file_path':'images/'+rn,'depth_file_path':'depth/'+rn,'transform_matrix':mat(g[3:7],g[:3])});assoc.append({'rgb_timestamp':t,'rgb_path':r,'depth_path':d,'pose': ' '.join(g)})
 (out/'transforms.json').write_text(json.dumps({'camera_model':'OPENCV','fl_x':517.3,'fl_y':516.5,'cx':318.6,'cy':255.3,'w':640,'h':480,'frames':frames},indent=2)); x.result_dir.mkdir(parents=True,exist_ok=True)
 with (x.result_dir/'tum_association_summary.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=['valid_triple_count','selected_frame_count','threshold_s']);w.writeheader();w.writerow({'valid_triple_count':n,'selected_frame_count':len(frames),'threshold_s':.02})
 with (x.result_dir/'tum_selected_frames_summary.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(assoc[0]));w.writeheader();w.writerows(assoc)
 print('selected_frames='+str(len(frames)))
if __name__=='__main__':main()
