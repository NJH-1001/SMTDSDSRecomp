"""Check final ZIP membership, source hashes and native setup architecture."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def architecture(data):
    if data[:2]==b"MZ":
        pe=struct.unpack_from("<I",data,0x3c)[0]
        if data[pe:pe+4]==b"PE\0\0" and struct.unpack_from("<H",data,pe+4)[0]==0x8664:return "Windows-x86_64"
    if data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<H",data,18)[0]==62:return "Linux-x86_64"
    if data[:4]==b"\xcf\xfa\xed\xfe":
        cpu=struct.unpack_from("<I",data,4)[0]
        if cpu==0x01000007:return "macOS-x86_64"
        if cpu==0x0100000c:return "macOS-arm64"
    raise RuntimeError("Unexpected native executable architecture")


def audit(path,platform):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise RuntimeError("Duplicate ZIP member")
        manifest=json.loads(archive.read("SOURCE_MANIFEST.json"))
        setup="SMTDSDSRecomp-Setup"+(".exe" if platform.startswith("Windows") else "")
        if set(names)!=set(manifest["files"])|{"SOURCE_MANIFEST.json",setup}:
            raise RuntimeError("Unexpected ZIP contents")
        for name,digest in manifest["files"].items():
            p=Path(name)
            if p.is_absolute() or ".." in p.parts or ".git" in p.parts:raise RuntimeError("Unsafe ZIP path")
            if p.suffix.lower() in {".nds",".rom",".bin",".sav",".dsv",".bmp",".png",".pdb",".exe",".dll"}:raise RuntimeError("Private payload filename")
            if hashlib.sha256(archive.read(name)).hexdigest()!=digest:raise RuntimeError(f"Source hash mismatch: {name}")
        data=archive.read(setup)
        if architecture(data)!=platform or len(data)>8*1024*1024 or b"SMTDSDSRecomp ROM-free setup 0.1.0" not in data:
            raise RuntimeError("Unexpected setup executable")
    return {"file":path.name,"platform":platform,"files":len(names),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"audit":"pass"}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("archive",type=Path);parser.add_argument("--platform",required=True)
    args=parser.parse_args();print(json.dumps(audit(args.archive,args.platform),indent=2))
