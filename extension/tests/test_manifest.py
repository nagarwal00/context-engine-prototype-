"""
Tests for Chrome Extension Manifest V3 configuration (Step 8.1).
Verifies:
- manifest_version is 3.
- Minimal permissions allowlist (only identity, storage, alarms).
- No dangerous broad permissions (<all_urls>, tabs, scripting).
- host_permissions restricted to github.com and CIF backend origins.
- All icon files exist and are valid PNG images.
- Content script matches only https://github.com/*/* with document_idle.
"""
import os
import json
import unittest


class TestExtensionManifest(unittest.TestCase):
    def setUp(self):
        self.extension_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.manifest_path = os.path.join(self.extension_dir, "manifest.json")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_manifest_version_is_3(self):
        self.assertEqual(self.manifest.get("manifest_version"), 3)

    def test_minimal_permissions(self):
        permissions = self.manifest.get("permissions", [])
        expected_permissions = {"identity", "storage", "alarms"}
        self.assertEqual(set(permissions), expected_permissions)
        # Verify no excessive permissions
        disallowed = {"<all_urls>", "tabs", "scripting", "webRequest", "cookies"}
        for p in permissions:
            self.assertNotIn(p, disallowed, f"Disallowed permission requested: {p}")

    def test_host_permissions_bounded(self):
        host_perms = self.manifest.get("host_permissions", [])
        self.assertIn("https://github.com/*", host_perms)
        # Ensure no wildcard internet access
        for h in host_perms:
            self.assertNotEqual(h, "<all_urls>")
            self.assertNotEqual(h, "*://*/*")
            self.assertNotEqual(h, "http://*/*")
            self.assertNotEqual(h, "https://*/*")

    def test_content_scripts_scoped(self):
        content_scripts = self.manifest.get("content_scripts", [])
        self.assertEqual(len(content_scripts), 1)
        cs = content_scripts[0]
        self.assertEqual(cs.get("matches"), ["https://github.com/*/*"])
        self.assertEqual(cs.get("run_at"), "document_idle")
        js_file = cs.get("js", [])[0]
        full_js_path = os.path.join(self.extension_dir, js_file)
        self.assertTrue(os.path.exists(full_js_path), f"Content script file missing: {full_js_path}")

    def test_all_icons_exist(self):
        icons = self.manifest.get("icons", {})
        for size in ("16", "32", "48", "128"):
            icon_rel = icons.get(size)
            self.assertIsNotNone(icon_rel, f"Missing icon for size {size}")
            icon_full = os.path.join(self.extension_dir, icon_rel)
            self.assertTrue(os.path.exists(icon_full), f"Icon file missing: {icon_full}")
            with open(icon_full, "rb") as f:
                header = f.read(8)
                self.assertEqual(header, b"\x89PNG\r\n\x1a\n", f"Invalid PNG header: {icon_full}")

    def test_stable_development_key(self):
        key = self.manifest.get("key")
        self.assertIsNotNone(key, "manifest.json should contain a stable development key")
        self.assertTrue(len(key) > 50, "key should be a valid base64 public key")


if __name__ == "__main__":
    unittest.main()
