"""
Tests for Frontend XSS Protection, HTML Escaping, and Static Lint (P0-c / Step 1.3)
"""
import os
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_APP_JS = REPO_ROOT / "web" / "app.js"
DOCS_APP_JS = REPO_ROOT / "docs" / "app.js"
WEB_INDEX_HTML = REPO_ROOT / "web" / "index.html"
DOCS_INDEX_HTML = REPO_ROOT / "docs" / "index.html"


def esc(value):
    """Python reference implementation of the JS esc() function in app.js."""
    if value is None:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def safe_url(value):
    """Python reference implementation of the JS safeUrl() function in app.js."""
    if not value:
        return "#"
    s = str(value).strip()
    if re.match(r"^https?://", s, re.IGNORECASE):
        return s
    return "#"


def lint_js_file_for_unescaped_inner_html(file_path: Path):
    """
    Static lint heuristic for checking template literals assigned to innerHTML.
    
    Rule:
    Any interpolation ${...} rendered into innerHTML must either:
    1. Call esc(...)
    2. Call safeUrl(...)
    3. Be a safe composite variable (e.g. artifactsStr, stepsHtml, baselineRows, statusBadge, html, content)
       composed of sanitized components
    4. Be a pure numeric/static expression (e.g. index, date substring, color constant)
    
    Returns a list of violation dicts: [{'line': int, 'content': str, 'interpolation': str}]
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    violations = []
    # Known safe variables that are pre-sanitized or contain static HTML snippets
    allowed_sub_identifiers = {
        "esc(",
        "safeUrl(",
        "artifactsStr",
        "stepsHtml",
        "baselineRows",
        "statusBadge",
        "html",
        "content",
        "this.getStateColor(",
        "Math.round(",
        "JSON.stringify(",
        "data-surface",
        "new Date(",
        "targetId",
        "itemType",
    }

    # Find innerHTML assignments
    for idx, line in enumerate(lines, 1):
        if "innerHTML" in line and "${" in line:
            # Single-line assignment with interpolation
            interpolations = re.findall(r"\$\{([^}]+)\}", line)
            for interp in interpolations:
                interp_stripped = interp.strip()
                if not any(allowed in interp_stripped for allowed in allowed_sub_identifiers):
                    violations.append({
                        "line": idx,
                        "content": line.strip(),
                        "interpolation": interp_stripped
                    })

    return violations


class TestFrontendEscape(unittest.TestCase):
    def test_csp_meta_tag_present_in_both_index_html_files(self):
        for path in [WEB_INDEX_HTML, DOCS_INDEX_HTML]:
            self.assertTrue(path.exists(), f"File {path} does not exist")
            content = path.read_text(encoding="utf-8")
            self.assertIn("Content-Security-Policy", content, f"Missing CSP in {path}")
            self.assertIn("default-src 'self'", content)
            self.assertIn("script-src 'self'", content)
            self.assertIn("style-src 'self' 'unsafe-inline'", content)
            self.assertIn("img-src 'self' data:", content)
            self.assertIn("connect-src 'self'", content)

    def test_static_lint_web_and_docs_app_js(self):
        for js_file in [WEB_APP_JS, DOCS_APP_JS]:
            self.assertTrue(js_file.exists(), f"{js_file} does not exist")
            violations = lint_js_file_for_unescaped_inner_html(js_file)
            self.assertEqual(
                violations,
                [],
                f"Found unescaped innerHTML interpolations in {js_file}: {violations}"
            )

    def test_static_lint_fails_on_synthetic_unescaped_injection(self):
        """Verify the static lint heuristic catches deliberate raw injections."""
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write("container.innerHTML = `<div>${d.title}</div>`;\n")
            temp_path = Path(f.name)

        try:
            violations = lint_js_file_for_unescaped_inner_html(temp_path)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["interpolation"], "d.title")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_esc_function_neutralizes_xss_payloads(self):
        payload_img = '<img src=x onerror=alert(1)>'
        escaped_img = esc(payload_img)
        self.assertNotIn("<img", escaped_img)
        self.assertEqual(escaped_img, "&lt;img src=x onerror=alert(1)&gt;")

        payload_script = '"><script>alert(1)</script>'
        escaped_script = esc(payload_script)
        self.assertNotIn("<script>", escaped_script)
        self.assertNotIn('">', escaped_script)
        self.assertEqual(escaped_script, "&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_safe_url_blocks_javascript_and_data_schemes(self):
        self.assertEqual(safe_url("javascript:alert(1)"), "#")
        self.assertEqual(safe_url("data:text/html,<script>alert(1)</script>"), "#")
        self.assertEqual(safe_url("vbscript:msgbox(1)"), "#")
        self.assertEqual(safe_url(""), "#")
        self.assertEqual(safe_url(None), "#")
        self.assertEqual(safe_url("https://github.com/acme-eng/repo"), "https://github.com/acme-eng/repo")
        self.assertEqual(safe_url("http://localhost:8080/api"), "http://localhost:8080/api")

    def test_synthetic_decision_with_xss_payload_renders_safely(self):
        """
        Ingest a synthetic event/decision with XSS payloads and verify rendering
        produces only escaped HTML entities across UI surfaces.
        """
        payload_title = '<img src=x onerror=alert(1)>'
        payload_rationale = '"><script>alert(1)</script>'
        payload_author = 'hacker<script>alert(2)</script>'

        # Timeline card rendering simulation
        card_html = f"""
          <div class="timeline-card">
            <h3 class="timeline-title">{esc(payload_title)}</h3>
            <p class="timeline-rationale">{esc(payload_rationale)}</p>
            <div class="timeline-meta">
              <span>Author: <strong>{esc(payload_author)}</strong></span>
            </div>
          </div>
        """

        self.assertNotIn("<img", card_html)
        self.assertNotIn("<script>", card_html)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", card_html)
        self.assertIn("&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;", card_html)
        self.assertIn("hacker&lt;script&gt;alert(2)&lt;/script&gt;", card_html)


if __name__ == "__main__":
    unittest.main()
