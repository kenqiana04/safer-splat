#!/usr/bin/env python3
"""Create server-only, source-preserving diagnostic PLY variants exactly once."""
from __future__ import annotations
import re, struct
from pathlib import Path
import numpy as np
from numba import njit
from _common import ROOT, SCENE_ROOT, atomic_json, diagnostic_marker, sha256


def header_and_offset(path: Path):
    with path.open("rb") as f:
        header=b""
        while not header.endswith(b"end_header\n"):
            header+=f.readline()
    text=header.decode("ascii");nv=int(re.search(r"element vertex (\d+)",text).group(1));nf=int(re.search(r"element face (\d+)",text).group(1))
    return header,nv,nf,len(header)+nv*27


@njit(cache=True)
def roots_from_faces(data, nv):
    parent=np.arange(nv,dtype=np.uint32)
    offset=0
    while offset<len(data):
        count=int(data[offset]);offset+=1
        a=np.uint32(data[offset])|np.uint32(data[offset+1])<<8|np.uint32(data[offset+2])<<16|np.uint32(data[offset+3])<<24
        offset+=4
        for _ in range(1,count):
            b=np.uint32(data[offset])|np.uint32(data[offset+1])<<8|np.uint32(data[offset+2])<<16|np.uint32(data[offset+3])<<24
            offset+=4
            x=a
            while parent[x]!=x:
                parent[x]=parent[parent[x]];x=parent[x]
            y=b
            while parent[y]!=y:
                parent[y]=parent[parent[y]];y=parent[y]
            if x!=y: parent[y]=x
    for i in range(nv):
        x=np.uint32(i)
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        parent[i]=x
    return parent


def copy_flat(src: Path, dest: Path, component=False) -> dict:
    hdr,nv,_,offset=header_and_offset(src);dest.parent.mkdir(parents=True,exist_ok=True)
    with src.open("rb") as f: f.seek(len(hdr));vertices=bytearray(f.read(nv*27))
    if component:
        raw=np.memmap(src,dtype=np.uint8,mode="r",offset=offset)
        roots=roots_from_faces(raw,nv);roots.tofile(ROOT/"diagnostic_variants/vertex_component_root_u32.bin")
        colors=np.array([[235,70,70],[70,220,90],[75,130,240],[240,190,60],[190,70,220],[50,210,210]],dtype=np.uint8)
        for i in range(nv): vertices[i*27+24:i*27+27]=bytes(colors[int(roots[i])%len(colors)])
    else:
        for i in range(nv): vertices[i*27+24:i*27+27]=b"\xdf\x9b\x3c"
    with dest.open("wb") as out,src.open("rb") as f:
        out.write(hdr);out.write(vertices);f.seek(offset)
        while chunk:=f.read(8*1024*1024):out.write(chunk)
    return {"path":str(dest),"sha256":sha256(dest),"vertex_count":nv}


def double_sided(src: Path,dest:Path)->dict:
    hdr,nv,nf,offset=header_and_offset(src);new_hdr=re.sub(rb"element face \d+",f"element face {nf*2}".encode(),hdr)
    with dest.open("wb") as out,src.open("rb") as f:
        out.write(new_hdr);f.seek(len(hdr));out.write(f.read(nv*27));f.seek(offset)
        while chunk:=f.read(8*1024*1024):out.write(chunk)
        f.seek(offset)
        for _ in range(nf):
            n=f.read(1)[0];idx=struct.unpack("<"+"I"*n,f.read(4*n));out.write(bytes([n]));out.write(struct.pack("<"+"I"*n,*reversed(idx)))
    return {"path":str(dest),"sha256":sha256(dest),"source_face_count":nf,"diagnostic_face_count":nf*2,"label":"DIAGNOSTIC_FACE_DUPLICATION_ONLY"}


def main()->None:
    root=ROOT/"diagnostic_variants";src=SCENE_ROOT/"mesh.ply"
    a=copy_flat(src,root/"flat_untextured_same_geometry.ply")
    b=double_sided(src,root/"double_sided_diagnostic.ply")
    c=copy_flat(src,root/"component_flat_id.ply",component=True)
    alt=SCENE_ROOT/"habitat/mesh_semantic.ply"
    atomic_json(root/"diagnostic_asset_variant_identity.json",{"status":"PASS_DIAGNOSTIC_ONLY_VARIANTS","marker":diagnostic_marker(),"source_mesh":{"path":str(src),"sha256":sha256(src)},"variants":{"A_FLAT_UNTEXTURED_SAME_GEOMETRY":a,"B_DOUBLE_SIDED_DIAGNOSTIC":b,"C_COMPONENT_FLAT_ID":c,"D_OFFICIAL_ALTERNATE_ASSET_HANDLE":{"eligible":alt.exists(),"path":str(alt),"sha256":sha256(alt) if alt.exists() else None,"source":"existing official apartment_0 habitat semantic mesh"}},"formal_asset_replacement":False})

if __name__=="__main__":main()
