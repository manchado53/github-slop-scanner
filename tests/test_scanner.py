"""Offline tests for the scan loops using a fake GitHub client (no network)."""

import pytest

from slopscanner.scanner import parse_repo_ref, scan, scan_repo, scan_user


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

    def get_repo(self, full_name):
        return self._by_full.get(full_name)

    @property
    def _by_full(self):
        return {r.get("full_name"): r for r in self._user_repos}


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


@pytest.mark.parametrize("ref,expected", [
    ("https://github.com/owner/name", "owner/name"),
    ("http://github.com/owner/name/", "owner/name"),
    ("https://www.github.com/owner/name.git", "owner/name"),
    ("github.com/owner/name/tree/main/src", "owner/name"),
    ("owner/name", "owner/name"),
    ("https://github.com/owner", None),
    ("", None),
])
def test_parse_repo_ref(ref, expected):
    assert parse_repo_ref(ref) == expected


def test_scan_repo_by_url(slop_repo):
    client = FakeClient([slop_repo])
    out = scan_repo(client, "https://github.com/someuser/my-project")
    assert len(out) == 1
    assert out[0].full_name == "someuser/my-project"
    assert out[0].score >= 80


def test_scan_repo_missing(slop_repo):
    client = FakeClient([slop_repo])
    assert scan_repo(client, "https://github.com/nobody/nothing") == []


def test_scan_repo_bad_link():
    assert scan_repo(FakeClient([]), "not a url") == []


def test_search_scan_collects_until_target(slop_repo):
    # Page 1 has two slop repos; target 1 should stop after the first.
    client = FakeClient([], pages={1: [dict(slop_repo), dict(slop_repo)]})
    out = scan(client, query="x", target=1, min_score=60, max_pages=3)
    assert len(out) == 1
