# -*- coding: utf-8 -*-
"""
Downloads the auto-editor binaries that Hush bundles.

    python3 fetch_engines.py            # only the one for this machine
    python3 fetch_engines.py --all      # every platform

The binaries are not kept in git — they are ~30 MB each and belong to
another project. Release builds fetch them at build time.
"""

import argparse
import os
import platform
import sys
import urllib.request

VERSION = "29.3.1"
BASE = ("https://github.com/WyattBlue/auto-editor/releases/download/"
        f"{VERSION}")

BINARIES = [
    "auto-editor-macos-arm64",
    "auto-editor-macos-x86_64",
    "auto-editor-windows-amd64.exe",
    "auto-editor-linux-x86_64",
]

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "bin")


def for_this_machine():
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "auto-editor-windows-amd64.exe"
    if system == "Darwin":
        return ("auto-editor-macos-arm64" if machine in ("arm64", "aarch64")
                else "auto-editor-macos-x86_64")
    return "auto-editor-linux-x86_64"


def fetch(name):
    dst = os.path.join(BIN, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
        print(f"  {name} - already here")
        return
    url = f"{BASE}/{name}"
    print(f"  {name} - downloading...")
    req = urllib.request.Request(url, headers={"User-Agent": "hush"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r, \
                open(dst, "wb") as f:
            while True:
                chunk = r.read(1 << 18)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        print(f"    failed: {e}", file=sys.stderr)
        raise
    if not name.endswith(".exe"):
        os.chmod(dst, 0o755)
    print(f"    {os.path.getsize(dst) / 1024 / 1024:.0f} MB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="fetch binaries for every platform")
    args = ap.parse_args()

    os.makedirs(BIN, exist_ok=True)
    wanted = BINARIES if args.all else [for_this_machine()]
    print(f"auto-editor {VERSION} -> bin/")
    for name in wanted:
        fetch(name)
    print("done")


if __name__ == "__main__":
    main()
