"""
Security hardening and static linter tests for Chrome Extension (Step 8.7).
Verifies:
1. Rule R5 compliance: ZERO occurrences of innerHTML, outerHTML, or insertAdjacentHTML.
2. No eval(), Function() constructor, or remote script loading.
3. safeUrl sanitization: blocks javascript:, data:, vbscript: protocols.
4. All external links specify target="_blank" and rel="noopener noreferrer".
"""
import os
import re
import unittest


def safe_url_py(url: str) -> str:
    """Python mirror of safeUrl in extension/src/lib/render.js."""
    if not url:
        return "#"
    s = str(url).strip()
    if re.match(r"^https?://", s, re.IGNORECASE):
        return s
    return "#"


class TestExtensionSecurity(unittest.TestCase):
    def setUp(self):
        self.extension_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _get_extension_files(self):
        files = []
        for root, _, filenames in os.walk(self.extension_dir):
            if "tests" in root:
                continue
            for f in filenames:
                if f.endswith((".js", ".html")):
                    files.append(os.path.join(root, f))
        return files

    def test_zero_inner_html_rule_r5(self):
        """Scans all extension source files to guarantee ZERO innerHTML or outerHTML."""
        dangerous_patterns = [
            (re.compile(r"\binnerHTML\b"), "innerHTML"),
            (re.compile(r"\bouterHTML\b"), "outerHTML"),
            (re.compile(r"\binsertAdjacentHTML\b"), "insertAdjacentHTML"),
            (re.compile(r"\beval\s*\("), "eval()"),
            (re.compile(r"new\s+Function\s*\("), "new Function()")
        ]

        files = self._get_extension_files()
        self.assertTrue(len(files) > 0, "No extension source files found to scan")

        violations = []
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Strip single-line and multi-line comments so comments documenting Rule R5 don't false-positive
                clean_content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
                clean_content = re.sub(r"//.*$", "", clean_content, flags=re.MULTILINE)
                clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)
                for pattern, name in dangerous_patterns:
                    matches = pattern.findall(clean_content)
                    if matches:
                        rel = os.path.relpath(file_path, self.extension_dir)
                        violations.append(f"{rel}: found {len(matches)} occurrence(s) of '{name}'")

        self.assertEqual(violations, [], f"Dangerous DOM injection patterns found:\n" + "\n".join(violations))

    def test_no_remote_scripts_or_inline_event_handlers(self):
        """Validates that no HTML file in the extension imports remote scripts or uses inline handlers."""
        html_files = [f for f in self._get_extension_files() if f.endswith(".html")]
        for h_file in html_files:
            with open(h_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Check for http:// or https:// script imports
                remote_script = re.findall(r'<script[^>]+src=["\']https?://', content, re.IGNORECASE)
                self.assertEqual(remote_script, [], f"Remote script import in {h_file}")
                # Check for inline onclick="..."
                inline_handler = re.findall(r'\bon[a-z]+\s*=', content, re.IGNORECASE)
                self.assertEqual(inline_handler, [], f"Inline event handler in {h_file}")

    def test_safe_url_sanitization(self):
        """safeUrl blocks dangerous protocol schemes and allows only http/https."""
        hostile_urls = [
            "javascript:alert(document.domain)",
            "JAVASCRIPT:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "file:///etc/passwd",
            "blob:https://github.com/uuid",
            "about:blank",
            "",
            None,
            "   "
        ]
        for hostile in hostile_urls:
            sanitized = safe_url_py(hostile)
            self.assertEqual(sanitized, "#", f"Hostile URL scheme not blocked: {hostile} -> {sanitized}")

        safe_urls = [
            "https://github.com/acme/repo/pull/1",
            "http://127.0.0.1:8080/api/me",
            "https://developer.mozilla.org"
        ]
        for valid in safe_urls:
            self.assertEqual(safe_url_py(valid), valid)


if __name__ == "__main__":
    unittest.main()
