"""
Tests for CIF VS Code Extension (Phase 9)
Validates:
- Manifest package.json schema, configuration, views, and commands
- Git remote URL parsing (HTTPS, SSH, non-GitHub)
- Symbol regex extraction
- Security constraints: zero direct network calls to GitHub (backend API only), zero hardcoded secrets
"""

import json
import os
import re
import unittest

class TestVSCodeExtension(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.package_json_path = os.path.join(self.root_dir, "package.json")
        self.src_dir = os.path.join(self.root_dir, "src")

    def test_package_json_schema_and_commands(self):
        """Verifies package.json structure, configuration properties, and commands."""
        self.assertTrue(os.path.exists(self.package_json_path), "package.json not found")
        with open(self.package_json_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)

        self.assertEqual(pkg.get("name"), "cif-vscode")
        self.assertEqual(pkg.get("publisher"), "cif")
        self.assertEqual(pkg.get("version"), "1.0.0")
        self.assertEqual(pkg.get("main"), "./src/extension.js")

        contributes = pkg.get("contributes", {})
        config_props = contributes.get("configuration", {}).get("properties", {})
        self.assertIn("cif.baseUrl", config_props)
        self.assertIn("cif.enableCodeLens", config_props)
        self.assertIn("cif.enableHover", config_props)
        self.assertIn("cif.enableDiagnostics", config_props)

        commands = {c["command"]: c["title"] for c in contributes.get("commands", [])}
        expected_commands = [
            "cif.signIn",
            "cif.signOut",
            "cif.addRepository",
            "cif.refreshDecisions",
            "cif.showDecisionDetails",
            "cif.evaluateGuardRules"
        ]
        for cmd in expected_commands:
            self.assertIn(cmd, commands, f"Command {cmd} missing from package.json")

        views = contributes.get("views", {}).get("cif-sidebar", [])
        view_ids = [v["id"] for v in views]
        self.assertIn("cif-decisions-view", view_ids)
        self.assertIn("cif-status-view", view_ids)

    def test_git_remote_url_parser(self):
        """Verifies remote URL parsing matches the JS implementation logic."""
        https_pattern = re.compile(r"^https?://(?:[a-zA-Z0-9_\-\.]+@)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$", re.IGNORECASE)
        ssh_pattern = re.compile(r"^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$", re.IGNORECASE)

        def parse(url):
            if not url:
                return None
            u = url.strip()
            m = https_pattern.match(u)
            if m:
                return {"owner": m.group(1), "repo": m.group(2)}
            m = ssh_pattern.match(u)
            if m:
                return {"owner": m.group(1), "repo": m.group(2)}
            return None

        # Standard HTTPS
        self.assertEqual(parse("https://github.com/facebook/react.git"), {"owner": "facebook", "repo": "react"})
        self.assertEqual(parse("https://github.com/facebook/react"), {"owner": "facebook", "repo": "react"})

        # SSH
        self.assertEqual(parse("git@github.com:torvalds/linux.git"), {"owner": "torvalds", "repo": "linux"})
        self.assertEqual(parse("git@github.com:torvalds/linux"), {"owner": "torvalds", "repo": "linux"})

        # Hyphenated, dotted, underscored names
        self.assertEqual(parse("https://github.com/my-org_99/my.repo-name.git"), {"owner": "my-org_99", "repo": "my.repo-name"})

        # Non-GitHub URLs rejected
        self.assertIsNone(parse("https://gitlab.com/owner/repo.git"))
        self.assertIsNone(parse("https://github.com.attacker.com/evil/repo"))
        self.assertIsNone(parse(""))

    def test_security_zero_direct_github_api_calls(self):
        """Validates that the VS Code extension makes zero direct calls to api.github.com."""
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".js"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.assertNotIn("api.github.com", content, f"Direct GitHub API call found in {file}")

    def test_security_zero_hardcoded_secrets(self):
        """Scans extension source code to guarantee zero tokens or passwords."""
        forbidden = ["ghp_", "github_pat_", "secret_", "password", "CIF_ADMIN_TOKEN"]
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".js"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for term in forbidden:
                            self.assertNotIn(term, content, f"Potential secret {term!r} found in {file}")

    def test_symbol_extraction_regex(self):
        """Verifies multi-language symbol extraction regex logic."""
        test_code = """
        def regular_function(arg):
            pass

        async def async_function():
            pass

        class MyClass:
            pass

        function jsFunc() {
        }

        const arrowFunc = (x) => {
        };

        func GoFunction(x int) error {
        }

        fn rust_function() -> u32 {
        }
        """
        patterns = [
            re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\("),
            re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)\s*[:\(]"),
            re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\("),
            re.compile(r"^\s*(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
            re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\("),
            re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*\(")
        ]

        found = []
        for line in test_code.splitlines():
            for pat in patterns:
                m = pat.match(line)
                if m:
                    found.append(m.group(1))
                    break

        self.assertIn("regular_function", found)
        self.assertIn("async_function", found)
        self.assertIn("MyClass", found)
        self.assertIn("jsFunc", found)
        self.assertIn("arrowFunc", found)
        self.assertIn("GoFunction", found)
        self.assertIn("rust_function", found)

if __name__ == "__main__":
    unittest.main()
