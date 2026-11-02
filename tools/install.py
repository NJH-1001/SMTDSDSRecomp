"""Build a private player from the user's dumps, without pre-existing captures.

Python 3.11+, CMake, Ninja, a C/C++ compiler and SDL3 development files required.
All proprietary inputs/outputs stay under --work; never publish that directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import time
import tomllib

from verify_inputs import identity

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA1 = "20a16088f0f1b67a11dd93a5a1976a702f8eaef7"
BOOT_RGB = "1852d602bb0bd94e6b0334292097ba7e4d16e8c1118b985b76bdc2d19e72d586"


def executable(directory: Path, name: str) -> Path:
    return directory / (name + (".exe" if os.name == "nt" else ""))


class Installer:
    def __init__(self, args):
        self.args = args
        self.work = args.work.resolve()
        self.framework = args.framework.resolve()
        self.ui = args.ui.resolve()
        self.bank_dir = self.work / "banks"
        self.title_dir = self.work / "title-banks"
        self.rc = executable(self.work / "recompiler", "nds_recompile")
        self.log = self.work / "install.log"

    def run(self, *command):
        print("Running:", Path(str(command[0])).name, " ".join(str(x) for x in command[1:3]), flush=True)
        with self.log.open("ab") as log:
            subprocess.run([str(x) for x in command], check=True, stdout=log, stderr=subprocess.STDOUT)

    def generate(self, config, image, bank, output, shards=2, live=True):
        command = [self.rc, "--config", config, "--bin", image,
                   "--out", output, "--bank", bank, "--shards", str(shards)]
        if live:
            command.append("--validate-live-bytes")
        self.run(*command)

    def configure(self, directory, *, title, frontend):
        command = ["cmake", "-S", self.framework / "runner", "-B", directory, "-G", "Ninja",
                   "-DCMAKE_BUILD_TYPE=RelWithDebInfo", "-DNDS_BOOTSTRAP_FIRMWARE=ON",
                   "-DNDS_ENABLE_COMPUTE_RENDERER=OFF", f"-DNDS_GENERATED_DIR={self.bank_dir}",
                   f"-DNDS_RECOMP_UI_ROOT={self.ui}", f"-DNDS_TITLE_BANK_DIR={title}",
                   f"-DNDS_TITLE_ROM_SHA1={ROM_SHA1}", f"-DNDS_SDL_BACKEND={'SDL3' if frontend else 'NONE'}"]
        if self.args.prefix:
            command.append(f"-DCMAKE_PREFIX_PATH={self.args.prefix.resolve()}")
        self.run(*command)

    def promote(self, manifests, generation):
        ingest=self.work / f"coverage-{generation}"
        self.run(sys.executable,self.framework / "tools/ingest_coverage_manifests.py",*manifests,
                 "--out",ingest,"--images",self.work / "images","--rom-sha1",ROM_SHA1,"--bank-prefix","smtds")
        report=json.loads((ingest / "ingest-report.json").read_text())
        if report["manifests_rejected"] or report["manifests_incomplete"] or report["problems"]:
            raise RuntimeError("Locally captured code failed provenance verification")
        for config in sorted((ingest / "images").glob("*.toml")):
            bank=tomllib.loads(config.read_text())["program"]["id"]
            self.generate(config,config.with_suffix(".bin"),bank,self.title_dir)

    def capture(self, player, name):
        sys.path.insert(0, str(self.framework / "oracle"))
        from _client import DebugClient
        folder = self.work / name
        folder.mkdir(exist_ok=True)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        env = os.environ.copy()
        env.update(NDS_DEEP_TRACE="0", NDS_HOSTPROF="off")
        command = [str(player), str(self.work / "inputs"), "--serve", "--port", str(port),
                   "--rom", str(self.args.rom.resolve()), "--config", str(ROOT / "game.toml"),
                   "--no-save", "--firmware-state-path", str(folder / "firmware-state.bin"),
                   "--diagnostics-dir", str(folder / "diagnostics")]
        client = None
        with (folder / "runner.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=folder, env=env, stdout=log,
                                       stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                deadline = time.monotonic()+30
                while time.monotonic()<deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"Bank producer exited; see {folder / 'runner.log'}")
                    try:
                        client = DebugClient(port=port, timeout=900)
                        break
                    except OSError:
                        time.sleep(.1)
                if client is None:
                    raise RuntimeError("Bank producer did not start its local debug server")
                # One continuous real-BIOS boot, synchronized on a hardware
                # event. No direct boot, BIOS stubs or discovery overrides.
                result = client.cmd("run_to_event", event="vblank9", count=1200, stall=300000)
                if not result.get("reached") or result.get("terminal"):
                    raise RuntimeError(f"Bank production failed its hardware event: {result}")
                manifest = folder / "coverage.json"
                client.cmd("coverage_manifest", path=manifest.as_posix())
                pixels = b"".join(client.framebuffer(engine)[2] for engine in ("A", "B"))
                report = {"event": result, "coverage": client.cmd("static_coverage"),
                          "rgb_sha256": hashlib.sha256(pixels).hexdigest()}
                (folder / "report.json").write_text(json.dumps(report, indent=2))
                if report["rgb_sha256"] != BOOT_RGB:
                    raise RuntimeError(f"Clean build boot differs from verified screen hash: {report['rgb_sha256']}")
                return manifest, report
            finally:
                if client:
                    client.close()
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=15)

    def install(self):
        expected = json.loads((ROOT / "config/required-inputs.json").read_text())
        for record in expected["files"]:
            actual = identity(getattr(self.args, record["id"]))
            if any(actual[key] != record[key] for key in actual):
                raise RuntimeError(f"Unsupported {record['id']}; compare README hashes")
        for command in ("cmake", "ninja", "git"):
            if not shutil.which(command):
                raise RuntimeError(f"Install {command} and place it on PATH first")
        if self.work.exists() and not self.args.resume:
            raise RuntimeError("Choose a new empty --work directory; existing installs are never overwritten")
        if self.work.exists():
            for key,name in (("bios9","biosnds9.rom"),("bios7","biosnds7.rom"),("firmware","firmware.bin")):
                record=next(r for r in expected["files"] if r["id"]==key)
                if identity(self.work / "inputs" / name)["sha256"]!=record["sha256"]:
                    raise RuntimeError("Existing workspace does not have verified installer inputs")
        self.work.mkdir(parents=True,exist_ok=True)
        for folder in ("inputs", "banks", "title-banks", "images", "state"):
            (self.work / folder).mkdir(exist_ok=True)
        for key, name in (("bios9", "biosnds9.rom"), ("bios7", "biosnds7.rom"), ("firmware", "firmware.bin")):
            shutil.copyfile(getattr(self.args,key), self.work / "inputs" / name)
        # ROM remains in place. Only extracted private modules enter --work.
        with self.args.rom.open("rb") as stream:
            header = stream.read(0x200)
            for cpu,offset in (("arm9",0x20),("arm7",0x30)):
                start,entry,load,size = struct.unpack_from("<4I",header,offset)
                stream.seek(start)
                (self.work / f"images/{cpu}.bin").write_bytes(stream.read(size))
                shutil.copyfile(ROOT / f"config/{cpu}.toml", self.work / f"images/{cpu}.toml")
        self.run("cmake", "-S", self.framework / "recompiler", "-B", self.work / "recompiler", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release")
        self.run("cmake", "--build", self.work / "recompiler", "--target", "nds_recompile", "-j", self.args.jobs)
        from prepare_dependencies import prepare_freebios
        prepare_freebios(self.framework)
        for cpu in (9,7):
            self.generate(self.framework / f"bios/biosnds{cpu}.toml", self.work / f"inputs/biosnds{cpu}.rom", f"arm{cpu}_bios", self.bank_dir,1,False)
            self.generate(self.framework / f"bios/freebios{cpu}.toml", self.framework / f"third_party/freebios/drastic_bios_arm{cpu}.bin", f"freebios_arm{cpu}", self.bank_dir,1,False)
        for cpu in (9,7):
            self.generate(ROOT / f"config/arm{cpu}.toml", self.work / f"images/arm{cpu}.bin", f"smtds_arm{cpu}_main", self.title_dir,8)
        self.configure(self.work / "producer",title=self.title_dir,frontend=False)
        self.run("cmake", "--build", self.work / "producer", "--target", "nds_runner", "-j", self.args.jobs)
        manifest, producer_report = self.capture(executable(self.work / "producer", "nds_runner"),"production")
        manifests=[manifest]
        (self.title_dir / "registration-order.txt").write_text("smtds_arm9_main\nsmtds_arm7_main\n")
        player = executable(self.work / "player", "nds_runner")
        if not self.args.prefix:
            from bootstrap_sdl import prepare_sdl
            print("Building pinned SDL3 SDK locally",flush=True)
            self.args.prefix=prepare_sdl(self.work / "sdl-sdk",self.args.jobs)
        for generation in range(1,5):
            self.promote(manifests,generation)
            self.configure(self.work / "player",title=self.title_dir,frontend=True)
            self.run("cmake","--build",self.work / "player","--target","nds_runner","-j",self.args.jobs)
            manifest,final_report=self.capture(player,f"verification-{generation}")
            coverage=final_report["coverage"]
            if coverage["clean_ram_rejects9"] or coverage["clean_ram_rejects7"]:
                raise RuntimeError("Clean build rejected clean RAM execution")
            if coverage["tier3_insns9"]<=16 and coverage["tier3_insns7"]<=1:
                break
            print("Promoting newly exposed copied-code generations",coverage,flush=True)
            manifests.append(manifest)
        else:
            raise RuntimeError("Copied-code promotion did not reach the accepted bounded-interpreter ceiling")
        (self.work / "install.json").write_text(json.dumps({"format":1,"player":str(player),
            "rom":str(self.args.rom.resolve()),"config":str(ROOT / "game.toml"),
            "producer":producer_report,"verification":final_report},indent=2))
        print("Private player built and boot hash verified:", player, flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("rom","bios9","bios7","firmware","work"):
        parser.add_argument(f"--{key}",type=Path,required=True)
    bundled=ROOT / "deps"
    parser.add_argument("--framework",type=Path,default=(bundled if bundled.exists() else ROOT.parent) / "ndsrecomp")
    parser.add_argument("--ui",type=Path,default=(bundled if bundled.exists() else ROOT.parent) / "recomp-ui")
    parser.add_argument("--prefix",type=Path,help="CMake prefix containing SDL3 development files")
    parser.add_argument("--jobs",type=int,default=4)
    parser.add_argument("--resume",action="store_true",help="Retry an interrupted private build after verifying its existing input copies")
    args=parser.parse_args()
    try:
        Installer(args).install()
    except (OSError,RuntimeError,subprocess.CalledProcessError) as error:
        print(f"Installation stopped: {error}\nPrivate log: {args.work / 'install.log'}",file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
