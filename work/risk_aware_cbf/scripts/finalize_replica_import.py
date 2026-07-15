#!/usr/bin/env python3
"""Normalize, hash, combine, and verify user-imported Replica v1 parts externally."""
from __future__ import annotations

import argparse, csv, hashlib, os, shutil, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path('/disk1/zlab/cross_dataset_assets')
NAMES = [f'replica_v1_0.tar.gz.parta{chr(i)}' for i in range(ord('a'), ord('q') + 1)]
SIZES = {name: 2_000_000_000 for name in NAMES}; SIZES[NAMES[-1]] = 1_859_047_808

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def csv_out(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['notes']); w.writeheader(); w.writerows(rows)

def safe_members(archive: Path, member_file: Path) -> tuple[bool, int, str]:
    try:
        with tarfile.open(archive, 'r:gz') as t, member_file.open('w', encoding='utf-8') as out:
            count = 0
            for m in t:
                p = PurePosixPath(m.name); out.write(m.name + '\n'); count += 1
                if p.is_absolute() or '..' in p.parts or m.issym() or m.islnk(): return False, count, f'unsafe_member:{m.name}'
        return count > 0, count, ''
    except (OSError, tarfile.TarError) as e: return False, 0, f'{type(e).__name__}:{e}'

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--asset-root', type=Path, default=ROOT); ap.add_argument('--result-dir', type=Path, required=True); ap.add_argument('--combine', action='store_true'); args = ap.parse_args()
    root, down, result = args.asset_root.resolve(), args.asset_root.resolve()/'downloads', args.result_dir
    quarantine = root/'tmp/replica_duplicate_quarantine'; quarantine.mkdir(parents=True, exist_ok=True)
    rows, resolutions, complete = [], [], True
    for name in NAMES:
        final, partial = down/name, down/(name + '.import.partial'); expected = SIZES[name]
        state = 'missing'; renamed = False; duplicate = final.exists() and partial.exists()
        if final.exists() and final.stat().st_size == expected: state = 'final_size_valid'
        elif not final.exists() and partial.exists() and partial.stat().st_size == expected:
            before = digest(partial); os.fsync(os.open(partial, os.O_RDONLY)); os.replace(partial, final); renamed = True
            state = 'partial_promoted' if before == digest(final) else 'promotion_hash_mismatch'
        elif partial.exists(): state = 'incomplete_transfer'
        if duplicate:
            target = quarantine/(partial.name + '.bak'); os.replace(partial, target); resolutions.append({'part_name':name,'partial_path':str(partial),'quarantine_path':str(target),'action':'quarantined_duplicate'})
        elif renamed: resolutions.append({'part_name':name,'partial_path':str(partial),'quarantine_path':'','action':'atomic_rename'})
        actual = final.stat().st_size if final.exists() else None; passed = actual == expected
        complete &= passed and state in {'final_size_valid','partial_promoted'}
        rows.append({'part_name':name,'source_path':str(final if final.exists() else partial),'source_state':state,'expected_size':expected,'actual_size':actual,'size_passed':passed,'sha256':digest(final) if passed else '', 'atomic_rename_performed':renamed,'duplicate_present':duplicate,'final_path':str(final),'final_status':state,'notes':''})
    csv_out(result/'replica_part_inventory.csv', rows); csv_out(result/'replica_part_hashes.csv', [{'part_name':r['part_name'],'sha256':r['sha256']} for r in rows]); csv_out(result/'replica_partial_resolution.csv', resolutions or [{'notes':'no_partial_action'}])
    if not args.combine or not complete: print('replica_parts_complete=' + str(complete)); return 0 if complete else 2
    temp, final = down/'replica_v1_0.tar.gz.import.partial', down/'replica_v1_0.tar.gz'
    if temp.exists(): os.replace(temp, quarantine/(temp.name + '.stale'))
    with temp.open('wb') as out:
        for name in NAMES:
            with (down/name).open('rb') as src: shutil.copyfileobj(src, out, 1024 * 1024)
        out.flush(); os.fsync(out.fileno())
    valid, members, note = safe_members(temp, root/'manifests/replica_archive_members.txt')
    size_ok = temp.stat().st_size == sum(SIZES.values()); before = digest(temp)
    if valid and size_ok:
        os.replace(temp, final); after = digest(final)
    else: after = ''
    csv_out(result/'replica_combined_archive_summary.csv', [{'archive_path':str(final if final.exists() else temp),'combined_size':final.stat().st_size if final.exists() else temp.stat().st_size,'expected_size':sum(SIZES.values()),'size_passed':size_ok,'sha256_before_rename':before,'sha256_after_rename':after,'tar_scan_passed':valid,'member_count':members,'path_traversal_safe':valid,'notes':note}])
    print('replica_archive_ready=' + str(valid and size_ok and before == after)); return 0 if valid and size_ok and before == after else 3

if __name__ == '__main__': raise SystemExit(main())
