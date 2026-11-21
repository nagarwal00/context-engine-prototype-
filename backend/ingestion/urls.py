"""
Citation locators for ingested events.

GitHub repositories get real https://github.com/... permalinks. Repositories ingested from a
local folder are named "local/<folder>" and have no web address: they previously received
https://github.com/local/<folder>/... links, which 404 while looking like verifiable evidence
(audit finding INT-04). They now get a non-clickable local:// locator that still identifies
the exact commit / file, e.g. local://demo_sample_repo/commit/<sha>.
"""


def is_local_repo(repo: str) -> bool:
    return repo.startswith("local/")


def citation_url(repo: str, kind: str, ref: str) -> str:
    """kind: 'commit' | 'issues' | 'pull' | 'blob'."""
    if is_local_repo(repo):
        folder = repo[len("local/"):]
        return f"local://{folder}/{kind}/{ref}"
    if kind == "blob":
        return f"https://github.com/{repo}/blob/main/{ref}"
    return f"https://github.com/{repo}/{kind}/{ref}"
