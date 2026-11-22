"""
JavaScript syntax check for the frontend and extensions (audit fix TOOL-02).

The previous version counted braces by hand and reported "Final brace depth: 1" for valid
code (template literals such as `${x}` confused it). This version asks Node.js to parse each
file (`node --check`) and exits non-zero on the first real syntax error. If Node.js is not
installed it says so and exits 0 (the Python test suite does not depend on it).
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = ["web", "extension/src", "vscode-extension/src"]


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("[SKIP] node not found; JavaScript syntax not checked")
        return 0
    files = sorted(p for t in TARGETS for p in (ROOT / t).rglob("*.js"))
    failed = 0
    for path in files:
        res = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        if res.returncode != 0:
            failed += 1
            print(f"[FAIL] {path.relative_to(ROOT)}\n{res.stderr.strip()}")
    print(f"[{'OK' if not failed else 'FAIL'}] {len(files) - failed}/{len(files)} JavaScript files parse")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
