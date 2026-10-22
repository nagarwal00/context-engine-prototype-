"""
test_no_clock_dependence.py - Guard against clock-dependent test fixtures.
Scans tests/*.py for patterns that bind static dates to expiring fields.
"""
import glob
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESTS_DIR = os.path.join(REPO_ROOT, "tests")

FORBIDDEN_PATTERNS = [
    (re.compile(r"verified_at.*20[0-9]{2}-", re.IGNORECASE), "verified_at with hardcoded timestamp"),
    (re.compile(r"expires.*20[0-9]{2}-", re.IGNORECASE), "expires with hardcoded timestamp"),
]


class TestNoClockDependence(unittest.TestCase):
    def test_no_hardcoded_expiry_or_verification_timestamps(self):
        test_files = glob.glob(os.path.join(TESTS_DIR, "*.py"))
        self.assertTrue(len(test_files) > 0, "No test files found in tests/")

        violations = []
        for file_path in test_files:
            # Skip this test file itself
            if os.path.basename(file_path) == "test_no_clock_dependence.py":
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, 1):
                    for pattern, desc in FORBIDDEN_PATTERNS:
                        if pattern.search(line):
                            violations.append(
                                f"{os.path.basename(file_path)}:{line_idx} - {desc}: {line.strip()}"
                            )

        self.assertEqual(
            violations,
            [],
            f"Found clock-dependent fixtures in tests:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
