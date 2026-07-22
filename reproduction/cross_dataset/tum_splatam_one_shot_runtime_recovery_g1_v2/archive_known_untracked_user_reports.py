"""Archive only the explicitly authorized untracked reports, then relocate them."""
from __future__ import annotations
import hashlib,json,mimetypes,os,shutil,subprocess,tarfile
from pathlib import Path
REPO=Path('/disk1/zlab/projects/safer-splat')
ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2')
KNOWN={
 'work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_CANDIDATE_EVALUATION_V0.md',
 'work/risk_aware_cbf/REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md',
 'work/risk_aware_cbf/paper_materials/VANS_ACTION_SEMANTICS_AUDIT.md',
}
def digest(p,kind):
 h=hashlib.new(kind)
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def info(p,rel):
 st=p.stat(); text=p.read_text(errors='replace').splitlines()
 return {'absolute_path':str(p),'relative_path':rel,'size':st.st_size,'mode':oct(st.st_mode & 0o777),'uid':st.st_uid,'gid':st.st_gid,'mtime_ns':st.st_mtime_ns,'sha256':digest(p,'sha256'),'blake2b':digest(p,'blake2b'),'line_count':len(text),'mime':mimetypes.guess_type(str(p))[0] or 'application/octet-stream','first_5_lines':text[:5],'last_5_lines':text[-5:],'is_symlink':p.is_symlink(),'symlink_target':str(p.resolve()) if p.is_symlink() else None}
def main():
 ROOT.mkdir(parents=True,exist_ok=True); archive=ROOT/'user_file_archive'; archive.mkdir(exist_ok=True)
 status=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v2','--untracked-files=all'],text=True)
 tracked=[x for x in status.splitlines() if x and not x.startswith('? ')]
 untracked={x[2:] for x in status.splitlines() if x.startswith('? ')}
 if tracked: raise SystemExit('UNKNOWN_TRACKED_MODIFICATIONS')
 unknown=untracked-KNOWN
 if unknown and not all(x.startswith('work/risk_aware_cbf/') for x in unknown): raise SystemExit('UNKNOWN_UNTRACKED_OUTSIDE_AUTHORIZED_ROOT')
 selected=sorted(untracked)
 records=[]
 for rel in selected:
  src=REPO/rel; dst=archive/'repository_relative_paths'/rel;dst.parent.mkdir(parents=True,exist_ok=True); before=info(src,rel);shutil.copy2(src,dst,follow_symlinks=False); after=info(dst,rel)
  same=src.read_bytes()==dst.read_bytes()
  if not same or before['sha256']!=after['sha256'] or before['blake2b']!=after['blake2b']: raise SystemExit('ARCHIVE_VERIFICATION_FAILED')
  records.append({'source':before,'archive':after,'byte_compare':same})
 tar=archive/'risk_aware_cbf_untracked_reports.tar'
 with tarfile.open(tar,'w') as t:
  for r in records:t.add(archive/'repository_relative_paths'/r['source']['relative_path'],arcname=r['source']['relative_path'],recursive=False)
 tar_sha=digest(tar,'sha256')
 manifest={'status':'PASS_KNOWN_USER_REPORTS_PRESERVED_AND_RELOCATED','files':records,'tar_path':str(tar),'tar_sha256':tar_sha}
 (archive/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 for r in records:(REPO/r['source']['relative_path']).unlink()
 final=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain=v2','--untracked-files=all'],text=True)
 if final.strip(): raise SystemExit('REPOSITORY_NOT_CLEAN_AFTER_AUTHORIZED_RELOCATION')
 (archive/'summary.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':manifest['status'],'count':len(records),'tar_sha256':tar_sha},sort_keys=True))
if __name__=='__main__':main()
