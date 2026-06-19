"""Offline tests for the scan loops using a fake GitHub client (no network)."""

from slopscanner.scanner import scan, scan_user


class FakeClient:
    """Stands in for GitHubClient: serves canned repos, enrich is a no-op."""

    def __init__(self, repos, pages=None):
        self._user_repos = repos
        self._pages = pages or {}

    def rate_limit_ok(self):
        return True

    def list_user_repos(self, username, *, include_forks=False, max_repos=300):
        return list(self._user_repos)

    def search_repos(self, query, page=1, per_page=30):
        return list(self._pages.get(page, []))

    def enrich(self, repo, *, sample_files=3):
        return repo  # fixtures already carry enriched fields


def test_scan_user_scores_all_and_sorts(slop_repo, good_repo):
    client = FakeClient([good_repo, slop_repo])
    out = scan_user(client, "someuser")
    assert len(out) == 2                      # min_score 0 -> everything shown
    assert out[0].score >= out[1].score       # sorted, sloppiest first
    assert out[0].full_name == slop_repo["full_name"]


def test_scan_user_respects_min_score(slop_repo, good_repo):
    client = FakeClient([good_repo, slop_repo])
    out = scan_user(client, "someuser", min_score=60)
    assert len(out) == 1
    assert out[0].full_name == slop_repo["full_name"]


def test_scan_user_handles_missing_user():
    out = scan_user(FakeClient([]), "ghost")
    assert out == []


def test_search_scan_collects_until_target(slop_repo):
    # Page 1 has two slop repos; target 1 should stop after the first.
    client = FakeClient([], pages={1: [dict(slop_repo), dict(slop_repo)]})
    out = scan(client, query="x", target=1, min_score=60, max_pages=3)
    assert len(out) == 1
