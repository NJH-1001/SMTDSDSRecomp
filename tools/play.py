"""Launch a completed private install with persistent saves and settings."""
import argparse
import json
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--work",type=Path,required=True)
args=parser.parse_args()
work=args.work.resolve()
record=json.loads((work / "install.json").read_text())
command=[record["player"],str(work / "inputs"),"--interactive","--rom",record["rom"],
         "--config",record["config"],"--save-path",str(work / "state/DevilSurvivor.sav"),
         "--firmware-state-path",str(work / "state/firmware.bin"),
         "--runtime-settings-path",str(work / "state/settings.ini"),
         "--diagnostics-dir",str(work / "state/diagnostics")]
raise SystemExit(subprocess.call(command,cwd=work))
