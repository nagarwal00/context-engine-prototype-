"""
Unit tests for tools/check_eol.py
Verifies that line ending changes (e.g. CRLF to LF or vice versa) are detected.
"""
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHECK_EOL_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_eol.py")


class TestCheckEOL(unittest.TestCase):
    def test_detects_crlf_to_lf_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=temp_dir, check=True)

            file_path = os.path.join(temp_dir, "test_file.txt")
            with open(file_path, "wb") as f:
                f.write(b"line 1\r\nline 2\r\nline 3\r\n")

            subprocess.run(["git", "add", "test_file.txt"], cwd=temp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "init with CRLF"], cwd=temp_dir, check=True)

            # Change to LF
            with open(file_path, "wb") as f:
                f.write(b"line 1\nline 2\nline 3\n")

            proc = subprocess.run([sys.executable, CHECK_EOL_SCRIPT], cwd=temp_dir, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("EOL CHANGED: test_file.txt", proc.stdout)

            # Revert to CRLF with an edit
            with open(file_path, "wb") as f:
                f.write(b"line 1\r\nline 2\r\nline 3 edited\r\n")

            proc_ok = subprocess.run([sys.executable, CHECK_EOL_SCRIPT], cwd=temp_dir, capture_output=True, text=True)
            self.assertEqual(proc_ok.returncode, 0)
            self.assertIn("EOL OK", proc_ok.stdout)


if __name__ == "__main__":
    unittest.main()
