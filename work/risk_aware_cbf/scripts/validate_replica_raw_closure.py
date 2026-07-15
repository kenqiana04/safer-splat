#!/usr/bin/env python3
"""Safely extract and inventory externally stored Replica v1 assets."""
from __future__ import annotations
import argparse, csv, hashlib, os, shutil, tarfile
from pathlib import Path, PurePosixPath

ROOT=Path('/disk1/zlab/cross_dataset_assets')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def out(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['notes']);w.writeheader();w.writerows(rows)
def main():
 a=argparse.ArgumentParser();a.add_argument('--asset-root',type=Path,default=ROOT);a.add_argument('--result-dir',type=Path,required=True);a.add_argument('--extract',action='store_true');x=a.parse_args(); root=x.asset_root.resolve(); archive=root/'downloads/replica_v1_0.tar.gz'; final=root/'raw/replica/replica_v1'; stage=root/'raw/replica/replica_v1.extracting'; quarantine=root/'tmp/replica_duplicate_quarantine'
 if x.extract and not final.exists():
  if stage.exists(): os.replace(stage,quarantine/(stage.name+'.stale'))
  stage.mkdir(parents=True)
  with tarfile.open(archive,'r:gz') as t:
   for m in t:
    p=PurePosixPath(m.name); target=(stage/m.name).resolve()
    if p.is_absolute() or '..' in p.parts or m.issym() or m.islnk() or stage.resolve() not in target.parents and target!=stage.resolve(): raise RuntimeError('unsafe_member:'+m.name)
    t.extract(m,stage)
  os.replace(stage,final)
 scenes=[]; meshrows=[]
 for d in sorted(p for p in final.iterdir() if p.is_dir()) if final.exists() else []:
  files=list(d.rglob('*')); meshes=[p for p in files if p.is_file() and p.suffix=='.ply']; nav=[p for p in files if p.is_file() and p.suffix=='.navmesh']; textures=[p for p in files if p.is_dir() and p.name=='textures']; meta=[p for p in files if p.is_file() and p.name in {'semantic.json','semantic.bin','info_semantic.json'}]; complete=bool(meshes and nav and textures and meta and all(p.stat().st_size for p in meshes+nav))
  scenes.append({'scene_name':d.name,'mesh_exists':bool(meshes),'navmesh_exists':bool(nav),'textures_exists':bool(textures),'scene_metadata_exists':bool(meta),'file_count':len(files),'total_size':sum(p.stat().st_size for p in files if p.is_file()),'scene_complete':complete})
  meshrows += [{'scene_name':d.name,'kind':'mesh','path':str(p),'size':p.stat().st_size,'sha256':sha(p)} for p in meshes] + [{'scene_name':d.name,'kind':'navmesh','path':str(p),'size':p.stat().st_size,'sha256':sha(p)} for p in nav]
 out(x.result_dir/'replica_scene_integrity_summary.csv',scenes or [{'scene_name':'','scene_complete':False}]);out(x.result_dir/'replica_mesh_navmesh_inventory.csv',meshrows or [{'notes':'no_assets'}]);out(x.result_dir/'replica_directory_inventory.csv',[{'path':str(final),'exists':final.exists(),'total_size':sum(p.stat().st_size for p in final.rglob('*') if p.is_file()) if final.exists() else 0}]);print('scene_count='+str(len(scenes)));return 0
if __name__=='__main__':raise SystemExit(main())
