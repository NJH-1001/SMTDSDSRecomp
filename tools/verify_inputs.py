"""Read-only verification of the user's local ROM, BIOS and firmware dumps.

No input is copied, modified, uploaded, or included in the JSON output.
Requires Python 3.9+; filenames may differ from the reference names.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[1]


def identity(path: Path) -> dict:
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    crc = size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            crc = zlib.crc32(chunk, crc)
            sha1.update(chunk)
            sha256.update(chunk)
    return {"size": size, "crc32": f"{crc:08x}",
            "sha1": sha1.hexdigest(), "sha256": sha256.hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("rom", "bios9", "bios7", "firmware"):
        parser.add_argument(f"--{key}", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads((ROOT / "config/required-inputs.json").read_text())
    results = []
    for item in expected["files"]:
        try:
            actual = identity(getattr(args, item["id"]))
            mismatches = [key for key in actual if actual[key] != item[key]]
            results.append({"id": item["id"], "ok": not mismatches,
                            "mismatches": mismatches, "actual": actual})
        except OSError as error:
            results.append({"id": item["id"], "ok": False,
                            "error": type(error).__name__})
    print(json.dumps({"ok": all(row["ok"] for row in results),
                      "files": results}, indent=2))
    return 0 if all(row["ok"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
