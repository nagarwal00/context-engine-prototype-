#!/usr/bin/env python3
"""
tools/check_eol.py - Line-ending guard tool
Compares EOL style between HEAD and working copy for modified files.
"""
import os
import subprocess
import sys


def get_eol_counts(data: bytes):
    crlf = data.count(b"\r\n")
    bare_lf = data.count(b"\n") - crlf
    return crlf, bare_lf


def get_style(crlf: int, bare_lf: int):
    if crlf > 0 and bare_lf == 0:
        return "CRLF"
    if bare_lf > 0 and crlf == 0:
        return "LF"
    if crlf > 0 and bare_lf > 0:
        return "MIXED"
    return "NONE"


def main():
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
    except Exception as e:
        print(f"Error running git diff: {e}", file=sys.stderr)
        return 1

    changed = []
    for file_path in files:
        if not os.path.isfile(file_path):
            continue

        git_path = file_path.replace("\\", "/")
        show_proc = subprocess.run(["git", "show", f"HEAD:{git_path}"], capture_output=True)
        if show_proc.returncode != 0:
            continue

        head_bytes = show_proc.stdout
        if b"\x00" in head_bytes:
            continue

        try:
            with open(file_path, "rb") as f:
                work_bytes = f.read()
        except OSError:
            continue

        if b"\x00" in work_bytes:
            continue

        head_crlf, head_lf = get_eol_counts(head_bytes)
        work_crlf, work_lf = get_eol_counts(work_bytes)

        head_style = get_style(head_crlf, head_lf)
        work_style = get_style(work_crlf, work_lf)

        if head_style != "NONE" and work_style != "NONE" and head_style != work_style:
            print(f"EOL CHANGED: {file_path}")
            changed.append(file_path)

    if changed:
        return 1

    print("EOL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
