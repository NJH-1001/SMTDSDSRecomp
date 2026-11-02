"""Compile the portable player using original synthetic ARM loops, never dumps.

The fixture executable is a compiler/linker check, not a playable release asset.
"""
from pathlib import Path
import argparse
import hashlib
import os
import subprocess
import sys
from prepare_dependencies import prepare_freebios

ROOT=Path(__file__).resolve().parents[1]


def run(*args):subprocess.run([str(x) for x in args],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--prefix",type=Path,required=True)
    args=parser.parse_args();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    framework=ROOT / "deps/ndsrecomp";ui=ROOT / "deps/recomp-ui"
    prepare_freebios(framework)
    run("cmake","-S",framework / "recompiler","-B",work / "recompiler","-G","Ninja","-DCMAKE_BUILD_TYPE=Release")
    run("cmake","--build",work / "recompiler","--target","nds_recompile","-j","3")
    rc=work / "recompiler" / ("nds_recompile.exe" if os.name=="nt" else "nds_recompile")
    banks=work / "banks";banks.mkdir(exist_ok=True)
    # B . is an original one-instruction synthetic test, not a BIOS dump.
    original=bytes.fromhex("feffffea");image=work / "synthetic-arm.bin";image.write_bytes(original)
    for cpu in (9,7):
        for bank in (f"arm{cpu}_bios",f"freebios_arm{cpu}"):
            config=work / f"{bank}.toml";base=0xFFFF0000 if cpu==9 else 0
            config.write_text(f'[program]\nname = "Original compiler fixture"\nid = "{bank}"\ncpu = "arm{cpu}"\nisa = "'+('armv5te' if cpu==9 else 'armv4t')+f'"\nload_address = {base}\nsize = 4\nentry_pc = {base}\n[identity]\nsha1 = "{hashlib.sha1(original).hexdigest()}"\n[[entry_point]]\naddr = {base}\nmode = "arm"\n')
            run(rc,"--config",config,"--bin",image,"--out",banks,"--bank",bank,"--shards","1")
    run("cmake","-S",framework / "runner","-B",work / "player","-G","Ninja",
        "-DCMAKE_BUILD_TYPE=RelWithDebInfo","-DNDS_BOOTSTRAP_FIRMWARE=ON","-DNDS_ENABLE_COMPUTE_RENDERER=OFF",
        f"-DNDS_GENERATED_DIR={banks}",f"-DNDS_RECOMP_UI_ROOT={ui}",f"-DCMAKE_PREFIX_PATH={args.prefix.resolve()}")
    run("cmake","--build",work / "player","--target","nds_runner","-j","3")
    print("Synthetic-input native player compiler/linker check passed; not a gameplay test")


if __name__=="__main__":main()
