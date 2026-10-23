"""
tools/verify_db_untouched.py
Verifies that running run_demo.py and unittest suite never mutates shipped databases
(context_intelligence.db and whybench.db).
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def compute_hash(path: Path) -> str:
    if not path.exists():
        return "NOT_FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    ci_db = PROJECT_ROOT / "context_intelligence.db"
    wb_db = PROJECT_ROOT / "whybench.db"

    ci_before = compute_hash(ci_db)
    wb_before = compute_hash(wb_db)

    print("[VERIFY_DB] Initial DB SHA-256 hashes:")
    print(f"  context_intelligence.db: {ci_before}")
    print(f"  whybench.db:             {wb_before}")

    print("[VERIFY_DB] Running python run_demo.py...")
    demo_proc = subprocess.run([sys.executable, "run_demo.py"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if demo_proc.returncode != 0:
        print("[VERIFY_DB] FAIL: run_demo.py exited with non-zero code:", demo_proc.returncode, file=sys.stderr)
        print(demo_proc.stdout, file=sys.stderr)
        print(demo_proc.stderr, file=sys.stderr)
        return 1

    print("[VERIFY_DB] Running python -m unittest discover -s tests...")
    test_proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if test_proc.returncode != 0:
        print("[VERIFY_DB] FAIL: test suite exited with non-zero code:", test_proc.returncode, file=sys.stderr)
        print(test_proc.stdout, file=sys.stderr)
        print(test_proc.stderr, file=sys.stderr)
        return 1

    ci_after = compute_hash(ci_db)
    wb_after = compute_hash(wb_db)

    print("[VERIFY_DB] Post-run DB SHA-256 hashes:")
    print(f"  context_intelligence.db: {ci_after}")
    print(f"  whybench.db:             {wb_after}")

    changed = []
    if ci_before != ci_after:
        changed.append(f"context_intelligence.db modified (before: {ci_before}, after: {ci_after})")
    if wb_before != wb_after:
        changed.append(f"whybench.db modified (before: {wb_before}, after: {wb_after})")

    if changed:
        print("[VERIFY_DB] FAIL: Shipped database(s) mutated during tests or demo:", file=sys.stderr)
        for msg in changed:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    print("[VERIFY_DB] DB UNTOUCHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
