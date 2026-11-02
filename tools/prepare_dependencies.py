"""Fetch only pinned, open-source framework build dependencies locally."""
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request


def prepare_freebios(framework: Path):
    root=framework / "third_party/freebios";root.mkdir(parents=True,exist_ok=True)
    for cpu,wanted in ((9,"b85d6afdbf65d87c9ab11d4e7fb5ecfd6192ccf8"),(7,"eaab9b21610978f05a0eb14a9c8ff345698f56a2")):
        path=root / f"drastic_bios_arm{cpu}.bin"
        data=path.read_bytes() if path.exists() else urllib.request.urlopen(
            f"https://raw.githubusercontent.com/mstan/freebios/6d6cfb4953924e4abdaa130aedf71826a055508e/{path.name}",timeout=60).read()
        if hashlib.sha1(data).hexdigest()!=wanted:
            raise RuntimeError("Open-source FreeBIOS dependency failed its pinned identity")
        if not path.exists():path.write_bytes(data)
    (framework / "vendor/freebios").mkdir(parents=True,exist_ok=True)
    if not (framework / "vendor/freebios/freebios_images.cpp").exists():
        subprocess.run([sys.executable,str(framework / "tools/gen_freebios_embed.py")],check=True)
