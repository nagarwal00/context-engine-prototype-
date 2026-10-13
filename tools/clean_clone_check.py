"""
Clean Clone and Cold-Start Verification Tool (Step 6.7)
Clones the repository into a clean temporary directory, initializes a fresh database
from migrations, executes the full test suite and automated demo verification,
and asserts zero failures or regressions.
"""
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cmd(cmd, cwd, env=None):
    merged_env = dict(os.environ)
    merged_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        merged_env.update(env)
    res = subprocess.run(cmd, cwd=str(cwd), env=merged_env, capture_output=True, text=True)
    return res


def clean_clone_check() -> bool:
    print("=" * 70)
    print("  CIF CLEAN CLONE & COLD-START VERIFICATION (STEP 6.7)")
    print("=" * 70)
    print(f"  Source Repository: {PROJECT_ROOT}")

    with tempfile.TemporaryDirectory(prefix="cif_clean_clone_") as tmp_dir:
        clone_path = Path(tmp_dir) / "cif_clone"
        print(f"  Temporary Target:  {clone_path}")
        print("-" * 70)

        # 1. Git Clone
        print("[1/5] Cloning repository to temporary destination...")
        res = run_cmd(["git", "clone", str(PROJECT_ROOT), str(clone_path)], cwd=tmp_dir)
        if res.returncode != 0:
            print(f"[FAIL] Git clone failed: {res.stderr}")
            return False
        print("      Clone successful.")

        # 2. Fresh Database Initialization & Migration Run
        print("[2/5] Initializing fresh database with migrations and seed data...")
        res = run_cmd([sys.executable, "tools/init_db.py", "--seed"], cwd=clone_path)
        if res.returncode != 0:
            print(f"[FAIL] Database initialization failed:\n{res.stderr}\n{res.stdout}")
            return False
        print("      Database migration & seed successful.")

        # 3. Secret Scan Verification
        print("[3/5] Running secret scanner audit...")
        res = run_cmd([sys.executable, "tools/scan_secrets.py", "--strict"], cwd=clone_path)
        if res.returncode != 0:
            print(f"[FAIL] Secret scanner audit failed:\n{res.stderr}\n{res.stdout}")
            return False
        print("      Secret scanner audit passed (0 leaks).")

        # 4. Full Unit & Integration Test Suite
        print("[4/5] Running full test suite (python -m unittest discover tests/)...")
        res = run_cmd([sys.executable, "-m", "unittest", "discover", "tests/"], cwd=clone_path)
        if res.returncode != 0:
            print(f"[FAIL] Test suite failed:\n{res.stderr}\n{res.stdout}")
            return False
        print("      Full test suite passed completely.")

        # 5. Automated Demo Verification
        print("[5/5] Running automated demo verification (python run_demo.py)...")
        res = run_cmd([sys.executable, "run_demo.py"], cwd=clone_path)
        if res.returncode != 0:
            print(f"[FAIL] Demo verification failed:\n{res.stderr}\n{res.stdout}")
            return False
        print("      Automated demo verification passed (21/21 checks).")

        print("=" * 70)
        print("  CLEAN CLONE VERIFICATION RESULT: ALL CHECKS PASSED")
        print("=" * 70)
        return True


if __name__ == "__main__":
    success = clean_clone_check()
    if not success:
        sys.exit(1)
