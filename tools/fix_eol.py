#!/usr/bin/env python3
"""
tools/fix_eol.py - Automatically fixes EOL of modified files to match HEAD style.
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
    return "OTHER"


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
        head_style = get_style(head_crlf, head_lf)

        if head_style == "LF":
            fixed = work_bytes.replace(b"\r\n", b"\n")
            if fixed != work_bytes:
                with open(file_path, "wb") as f:
                    f.write(fixed)
                print(f"Fixed {file_path} -> LF")
        elif head_style == "CRLF":
            fixed = work_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if fixed != work_bytes:
                with open(file_path, "wb") as f:
                    f.write(fixed)
                print(f"Fixed {file_path} -> CRLF")

    return 0


if __name__ == "__main__":
    sys.exit(main())
