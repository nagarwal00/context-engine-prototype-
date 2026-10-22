"""
Build tool for CIF Chrome Extension (Step 8.8).
Packages extension/ directory into dist/cif-extension.zip, excluding
tests, documentation, and Python cache files.
"""

import os
import sys
import json
import zipfile

def build_extension_zip():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extension_dir = os.path.join(repo_root, "extension")
    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    manifest_path = os.path.join(extension_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    version = manifest.get("version", "unknown")
    name = manifest.get("name", "cif-extension")
    zip_path = os.path.join(dist_dir, f"cif-extension-v{version}.zip")
    latest_zip_path = os.path.join(dist_dir, "cif-extension.zip")

    exclude_patterns = [
        "tests",
        "__pycache__",
        ".pyc",
        ".md",
        ".DS_Store",
        "Thumbs.db"
    ]

    packaged_files = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extension_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]
            for file in files:
                if any(p in file for p in exclude_patterns):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, extension_dir)
                zf.write(full_path, rel_path)
                packaged_files.append(rel_path)

    # Also write dist/cif-extension.zip as canonical latest
    import shutil
    shutil.copyfile(zip_path, latest_zip_path)

    print(f"Successfully packaged {name} v{version}:")
    print(f"  Artifact: {zip_path}")
    print(f"  Latest symlink/copy: {latest_zip_path}")
    print(f"  Total files packaged: {len(packaged_files)}")
    for pf in sorted(packaged_files):
        print(f"    - {pf}")

if __name__ == "__main__":
    build_extension_zip()
