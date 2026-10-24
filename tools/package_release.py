"""
Release Packager and Clean Bundle Verifier (Step 6.3)
Packages the project into a release-quality ZIP archive:
- Strictly excludes .git/, *.db, backups/, __pycache__/, .env, editor dirs
- Ensures synthetic fixtures are shipped as source files/JSON, never live DB binaries
- Verifies package by extracting into a clean temp directory and executing the full test suite
"""
import os
import sys
import zipfile
import tempfile
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git",
    "backups",
    "scratch",
    "__pycache__",
    "dist",
    ".gemini",
    ".idea",
    ".vscode",
    "node_modules",
}

EXCLUDE_EXTENSIONS = {
    ".db",
    ".db-journal",
    ".sqlite",
    ".sqlite3",
    ".pyc",
    ".pyo",
    ".key",
    ".pem",
}

EXCLUDE_FILES = {
    ".env",
    ".DS_Store",
}


def should_exclude(rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if rel_path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True
    if rel_path.name in EXCLUDE_FILES:
        return True
    return False


def build_release_package(out_zip: Path) -> Path:
    out_zip = out_zip.resolve()
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    print(f"[PACKAGE] Building clean release package at: {out_zip}")

    included_count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            root_path = Path(root)
            # Prune excluded directories in-place so os.walk does not recurse into them
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for fname in files:
                fpath = root_path / fname
                rel_path = fpath.relative_to(PROJECT_ROOT)

                if should_exclude(rel_path):
                    continue

                zf.write(fpath, arcname=str(rel_path).replace("\\", "/"))
                included_count += 1

    print(f"[OK] Release package built with {included_count} files ({out_zip.stat().st_size / 1024:.1f} KB).")
    return out_zip


def verify_release_package(zip_path: Path) -> bool:
    print(f"[VERIFY] Testing release package extraction and test execution...")
    with tempfile.TemporaryDirectory(prefix="cif_verify_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)

        # 1. Assert no forbidden files exist in extracted package
        forbidden_found = []
        for root, dirs, files in os.walk(tmp_path):
            for d in dirs:
                if d in EXCLUDE_DIRS:
                    forbidden_found.append(os.path.join(root, d))
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in EXCLUDE_EXTENSIONS or f in EXCLUDE_FILES:
                    forbidden_found.append(os.path.join(root, f))

        if forbidden_found:
            print(f"[FAIL] Forbidden files found in release bundle: {forbidden_found[:5]}")
            return False

        print("[OK] Zero forbidden files (.git, *.db, backups, pycache, .env) in release package.")

        # 2. Verify database initialization on clean package
        print("[VERIFY] Initializing database and migrations inside clean package...")
        init_res = subprocess.run(
            [sys.executable, "tools/init_db.py", "--seed"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )
        if init_res.returncode != 0:
            print(f"[FAIL] tools/init_db.py failed inside extracted release package:\n{init_res.stderr}")
            return False

        print("[OK] Database initialization and seed runner verified in clean package.")

        # 3. Run unit tests inside the extracted clean package
        print("[VERIFY] Running full test suite inside extracted release directory...")
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "tests/"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        if res.returncode != 0:
            print(f"[FAIL] Test suite failed inside extracted release package:\n{res.stderr}")
            return False

        print(f"[OK] All unit tests passed inside clean extracted package!")

    return True


def main():
    parser = argparse.ArgumentParser(description="CIF Release Packager")
    parser.add_argument("--out", type=str, default=str(PROJECT_ROOT / "dist" / "cif_release.zip"), help="Output ZIP path")
    parser.add_argument("--skip-verify", action="store_true", help="Skip test verification")
    args = parser.parse_args()

    zip_path = Path(args.out)
    built_zip = build_release_package(zip_path)

    if not args.skip_verify:
        success = verify_release_package(built_zip)
        if not success:
            sys.exit(1)

    print(f"\n[SUCCESS] Release package verified and ready: {built_zip}")


if __name__ == "__main__":
    main()
