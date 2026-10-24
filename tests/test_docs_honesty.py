"""
tests/test_docs_honesty.py - Honesty guard test for benchmark provenance claims (Step 2.3)
Verifies that no tracked documentation, web, or benchmark files contain fabricated
provenance claims regarding WhyBench.
"""
import os
import subprocess
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_PHRASES = [
    "real-world benchmark",
    "pinned commit sha",
    "open-source repositories",
    "public github urls",
]

# Exact paths allowed to retain historical audit logs / quotes
ALLOWLIST = {
    "STATUS_AUDIT.md",
    "ANTIGRAVITY_HANDOFF_V4_FIXES.md",
    "ANTIGRAVITY_HANDOFF_V2.md",
    "ANTIGRAVITY_HANDOFF.md",
    "docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md",
    "docs/process/ANTIGRAVITY_HANDOFF_V2.md",
    "docs/process/ANTIGRAVITY_HANDOFF.md",
    "docs/process/ANTIGRAVITY_HANDOFF_V3_EXTENSION.md",
}


class TestDocsHonesty(unittest.TestCase):
    """Guards against fabricated provenance or real-world over-claims for WhyBench."""

    def test_no_fabricated_provenance_claims(self):
        try:
            proc = subprocess.run(
                ["git", "ls-files"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            tracked_files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        except Exception:
            tracked_files = []
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "backups", "scratch", "__pycache__"]]
                for f in files:
                    tracked_files.append(os.path.relpath(os.path.join(root, f), PROJECT_ROOT))

        violations = []
        for rel_path in tracked_files:
            norm_path = rel_path.replace("\\", "/")

            # Check allowlist
            if any(norm_path == allowed or norm_path.startswith("docs/process/") for allowed in ALLOWLIST):
                continue

            # Target tracked .md, .html, and .js files
            ext = os.path.splitext(norm_path)[1].lower()
            if ext not in [".md", ".html", ".js"]:
                continue

            full_path = os.path.join(PROJECT_ROOT, rel_path)
            if not os.path.isfile(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
            except OSError:
                continue

            for phrase in FORBIDDEN_PHRASES:
                if phrase in content:
                    violations.append(f"{norm_path}: contains forbidden phrase '{phrase}'")

        self.assertEqual(
            violations,
            [],
            f"Found forbidden provenance claims in tracked files:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
