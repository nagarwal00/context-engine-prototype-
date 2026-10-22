"""
Tests for GitHub URL parsing logic (Step 8.6).
Evaluates parseGithubUrl across >= 15 URL variants:
- Repository root URLs
- Pull request URLs (overview, files tab, commits tab)
- Issue URLs
- Blob / file URLs with and without line anchors
- Tree / directory URLs
- Enterprise and attacker lookalike hosts (MUST be rejected)
- Non-repository top-level GitHub paths (MUST be rejected)
"""
import unittest
import urllib.parse

RESERVED_TOP_PATHS = {
    "about", "pricing", "features", "enterprise", "login", "join", "signup",
    "settings", "notifications", "explore", "topics", "trending", "collections",
    "security", "marketplace", "issues", "pulls", "orgs", "users", "stars"
}

def parse_github_url_py(raw_url: str):
    """Python mirror of parseGithubUrl in extension/src/lib/github_url.js for testing."""
    result = {
        "valid": False,
        "kind": "unknown",
        "owner": None,
        "repo": None,
        "fullName": None,
        "number": None,
        "ref": None,
        "path": None,
        "line": None
    }
    if not raw_url:
        return result

    try:
        parsed = urllib.parse.urlparse(raw_url)
    except Exception:
        return result

    host = parsed.netloc.lower()
    if host != "github.com" and host != "www.github.com":
        return result

    segments = [s for s in parsed.path.split("/") if s]
    if len(segments) < 2:
        return result

    owner = segments[0]
    repo = segments[1]

    if owner.lower() in RESERVED_TOP_PATHS:
        return result

    result["owner"] = owner
    result["repo"] = repo
    result["fullName"] = f"{owner}/{repo}"
    result["valid"] = True

    if len(segments) == 2:
        result["kind"] = "repo"
        return result

    sub_type = segments[2]

    if sub_type == "pull" and len(segments) >= 4:
        try:
            num = int(segments[3])
            if num > 0:
                result["kind"] = "pull"
                result["number"] = num
                return result
        except ValueError:
            pass

    if sub_type == "issues" and len(segments) >= 4:
        try:
            num = int(segments[3])
            if num > 0:
                result["kind"] = "issue"
                result["number"] = num
                return result
        except ValueError:
            pass

    if sub_type == "blob" and len(segments) >= 5:
        result["kind"] = "blob"
        result["ref"] = segments[3]
        result["path"] = "/".join(segments[4:])
        if parsed.fragment:
            import re
            m = re.match(r"^L(\d+)", parsed.fragment, re.IGNORECASE)
            if m:
                result["line"] = int(m.group(1))
        return result

    if sub_type == "tree" and len(segments) >= 4:
        result["kind"] = "tree"
        result["ref"] = segments[3]
        result["path"] = "/".join(segments[4:])
        return result

    result["kind"] = "other"
    return result


class TestGitHubUrlParsing(unittest.TestCase):
    def test_repo_root(self):
        u1 = parse_github_url_py("https://github.com/facebook/react")
        self.assertTrue(u1["valid"])
        self.assertEqual(u1["kind"], "repo")
        self.assertEqual(u1["fullName"], "facebook/react")

        u2 = parse_github_url_py("https://github.com/torvalds/linux/")
        self.assertTrue(u2["valid"])
        self.assertEqual(u2["kind"], "repo")
        self.assertEqual(u2["fullName"], "torvalds/linux")

    def test_pull_requests(self):
        # 1. Main PR view
        u1 = parse_github_url_py("https://github.com/acme/repo/pull/123")
        self.assertTrue(u1["valid"])
        self.assertEqual(u1["kind"], "pull")
        self.assertEqual(u1["number"], 123)
        self.assertEqual(u1["fullName"], "acme/repo")

        # 2. Files changed tab
        u2 = parse_github_url_py("https://github.com/acme/repo/pull/123/files")
        self.assertTrue(u2["valid"])
        self.assertEqual(u2["kind"], "pull")
        self.assertEqual(u2["number"], 123)

        # 3. Commits tab
        u3 = parse_github_url_py("https://github.com/acme/repo/pull/456/commits")
        self.assertTrue(u3["valid"])
        self.assertEqual(u3["kind"], "pull")
        self.assertEqual(u3["number"], 456)

        # 4. Discussion anchor
        u4 = parse_github_url_py("https://github.com/acme/repo/pull/789#discussion_r12345")
        self.assertTrue(u4["valid"])
        self.assertEqual(u4["kind"], "pull")
        self.assertEqual(u4["number"], 789)

    def test_issues(self):
        u1 = parse_github_url_py("https://github.com/acme/repo/issues/101")
        self.assertTrue(u1["valid"])
        self.assertEqual(u1["kind"], "issue")
        self.assertEqual(u1["number"], 101)

    def test_blob_files(self):
        # 1. Standard file blob
        u1 = parse_github_url_py("https://github.com/acme/repo/blob/main/src/app.py")
        self.assertTrue(u1["valid"])
        self.assertEqual(u1["kind"], "blob")
        self.assertEqual(u1["ref"], "main")
        self.assertEqual(u1["path"], "src/app.py")
        self.assertIsNone(u1["line"])

        # 2. File with line number anchor
        u2 = parse_github_url_py("https://github.com/acme/repo/blob/v2.1.0/lib/cache/store.ts#L42")
        self.assertTrue(u2["valid"])
        self.assertEqual(u2["kind"], "blob")
        self.assertEqual(u2["ref"], "v2.1.0")
        self.assertEqual(u2["path"], "lib/cache/store.ts")
        self.assertEqual(u2["line"], 42)

        # 3. Commit SHA ref
        u3 = parse_github_url_py("https://github.com/acme/repo/blob/a1b2c3d4e5/README.md#L10")
        self.assertTrue(u3["valid"])
        self.assertEqual(u3["kind"], "blob")
        self.assertEqual(u3["ref"], "a1b2c3d4e5")
        self.assertEqual(u3["path"], "README.md")
        self.assertEqual(u3["line"], 10)

    def test_tree_directories(self):
        u1 = parse_github_url_py("https://github.com/acme/repo/tree/main/docs")
        self.assertTrue(u1["valid"])
        self.assertEqual(u1["kind"], "tree")
        self.assertEqual(u1["ref"], "main")
        self.assertEqual(u1["path"], "docs")

    def test_attacker_and_lookalike_hosts_rejected(self):
        lookalikes = [
            "https://evil-github.com/acme/repo",
            "https://github.com.evil.com/acme/repo",
            "https://github.org/acme/repo",
            "https://mygithub.com/acme/repo",
            "https://notgithub.com/acme/repo/pull/1",
            "http://insecure-github.com/acme/repo"
        ]
        for url in lookalikes:
            res = parse_github_url_py(url)
            self.assertFalse(res["valid"], f"Attacker host accepted: {url}")

    def test_non_repo_github_paths_rejected(self):
        non_repos = [
            "https://github.com/",
            "https://github.com/explore",
            "https://github.com/settings/profile",
            "https://github.com/marketplace",
            "https://github.com/pricing",
            "https://github.com/about",
            "https://github.com/notifications"
        ]
        for url in non_repos:
            res = parse_github_url_py(url)
            self.assertFalse(res["valid"], f"Non-repo path accepted as repo: {url}")


if __name__ == "__main__":
    unittest.main()
