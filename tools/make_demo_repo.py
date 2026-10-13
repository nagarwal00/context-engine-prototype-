"""
Deterministic Demo Git Repository Builder (Step 6.3)
Generates the demo sample repository on demand with exact commit histories,
authors, dates, and diffs, avoiding the need for tracked nested .git folders in release distributables.
"""
import os
import sys
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_SOURCE_DIR = PROJECT_ROOT / "demo_sample_repo"


def build_demo_repo(target_dir: Path) -> Path:
    target_dir = target_dir.resolve()
    print(f"[DEMO_REPO] Building deterministic demo git repository at: {target_dir}")

    # If target is different from source, copy all source files (excluding .git)
    if target_dir != DEMO_SOURCE_DIR:
        target_dir.mkdir(parents=True, exist_ok=True)
        for item in DEMO_SOURCE_DIR.iterdir():
            if item.name in (".git", "__pycache__"):
                continue
            dest = target_dir / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(dest))

    setup_script = target_dir / "setup_git_history.py"
    if not setup_script.exists():
        raise FileNotFoundError(f"Missing setup script at {setup_script}")

    # Run setup_git_history.py inside target directory
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )

    if res.returncode != 0:
        print(f"[ERROR] Failed to setup git history: {res.stderr}")
        raise RuntimeError(f"Git history generation failed: {res.stderr}")

    # Verify commit count
    rev_check = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=str(target_dir),
        capture_output=True,
        text=True
    )
    commit_count = rev_check.stdout.strip()
    print(f"[OK] Demo repository created successfully with {commit_count} commits at {target_dir}")
    return target_dir


def main():
    parser = argparse.ArgumentParser(description="Deterministic Demo Git Repository Generator")
    parser.add_argument("--target", type=str, default=None, help="Target directory to create repository in")
    parser.add_argument("--in-place", action="store_true", help="Rebuild git history in demo_sample_repo")
    args = parser.parse_args()

    if args.in_place:
        target = DEMO_SOURCE_DIR
    elif args.target:
        target = Path(args.target)
    else:
        target = Path(tempfile.mkdtemp(prefix="demo_repo_"))

    built_path = build_demo_repo(target)
    print(f"Result path: {built_path}")


if __name__ == "__main__":
    main()
