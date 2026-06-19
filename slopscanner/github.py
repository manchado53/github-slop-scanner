"""Thin GitHub REST API client focused on what the slop scanner needs.

Handles authentication, primary and secondary rate limits, and the few
endpoints we use: repo search, README, git tree, commit/contributor counts,
and a small sample of raw file contents for emoji detection.

We deliberately use plain ``requests`` (not PyGithub) so rate-limit handling
stays explicit and the dependency surface stays tiny.
"""

from __future__ import annotations

import base64
import time
from typing import Dict, List, Optional

import requests

API = "https://api.github.com"

# File extensions we'll sample for emoji-in-code detection.
_CODE_EXTS = (
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".cs", ".rs", ".swift", ".kt", ".sh",
)


class RateLimitError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: Optional[str], *, max_sleep: float = 60.0,
                 verbose: bool = False):
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-slop-scanner",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)
        self.token = token
        self.max_sleep = max_sleep
        self.verbose = verbose

    # -- low-level ----------------------------------------------------------

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[github] {msg}")

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Single request with rate-limit awareness and light retry."""
        for attempt in range(4):
            resp = self.session.request(method, url, timeout=30, **kwargs)

            # Primary rate limit exhausted.
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                wait = max(0.0, reset - time.time()) + 1
                if wait > self.max_sleep:
                    raise RateLimitError(
                        f"Rate limit hit; reset in {int(wait)}s "
                        f"(> max_sleep {self.max_sleep}s). Stopping."
                    )
                self._log(f"rate limited; sleeping {int(wait)}s")
                time.sleep(wait)
                continue

            # Secondary / abuse rate limit.
            if resp.status_code in (403, 429) and "retry-after" in resp.headers:
                wait = float(resp.headers["retry-after"]) + 1
                if wait > self.max_sleep:
                    raise RateLimitError(f"Secondary rate limit; retry-after {int(wait)}s.")
                self._log(f"secondary limit; sleeping {int(wait)}s")
                time.sleep(wait)
                continue

            if resp.status_code >= 500 and attempt < 3:
                time.sleep(1.5 * (attempt + 1))
                continue

            return resp

        return resp  # type: ignore[return-value]

    def _get_json(self, path: str, **params) -> Optional[dict]:
        url = path if path.startswith("http") else f"{API}{path}"
        resp = self._request("GET", url, params=params or None)
        if resp.status_code == 200:
            return resp.json()
        return None

    @staticmethod
    def _last_page_from_link(resp: requests.Response) -> Optional[int]:
        """Parse the 'last' page number from a Link header, if present."""
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            if 'rel="last"' in part:
                seg = part[part.find("<") + 1: part.find(">")]
                if "page=" in seg:
                    try:
                        return int(seg.split("page=")[-1].split("&")[0])
                    except ValueError:
                        return None
        return None

    def _count_via_pagination(self, path: str) -> Optional[int]:
        """Cheap total count: request 1 item/page, read 'last' page number."""
        url = f"{API}{path}"
        sep = "&" if "?" in path else "?"
        resp = self._request("GET", f"{url}{sep}per_page=1")
        if resp.status_code != 200:
            return None
        last = self._last_page_from_link(resp)
        if last is not None:
            return last
        data = resp.json()
        return len(data) if isinstance(data, list) else None

    # -- high-level endpoints ----------------------------------------------

    def search_repos(self, query: str, page: int = 1, per_page: int = 30,
                     sort: Optional[str] = None, order: str = "desc") -> List[dict]:
        params = {"q": query, "page": page, "per_page": per_page, "order": order}
        if sort:
            params["sort"] = sort
        data = self._get_json("/search/repositories", **params)
        if not data:
            return []
        return data.get("items", [])

    def get_readme(self, full_name: str) -> Optional[str]:
        data = self._get_json(f"/repos/{full_name}/readme")
        if not data:
            return None
        content = data.get("content")
        if not content:
            return None
        try:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except (ValueError, UnicodeDecodeError):
            return None

    def get_tree(self, full_name: str, branch: str) -> Optional[List[str]]:
        data = self._get_json(f"/repos/{full_name}/git/trees/{branch}", recursive=1)
        if not data:
            return None
        tree = data.get("tree", [])
        return [t["path"] for t in tree if t.get("type") == "blob"]

    def get_commits_count(self, full_name: str) -> Optional[int]:
        return self._count_via_pagination(f"/repos/{full_name}/commits")

    def get_contributors_count(self, full_name: str) -> Optional[int]:
        return self._count_via_pagination(f"/repos/{full_name}/contributors")

    def get_file_content(self, full_name: str, path: str) -> Optional[str]:
        data = self._get_json(f"/repos/{full_name}/contents/{path}")
        if not data or "content" not in data:
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except (ValueError, UnicodeDecodeError):
            return None

    # -- enrichment ---------------------------------------------------------

    def enrich(self, repo: dict, *, sample_files: int = 3) -> dict:
        """Augment a search-result repo with the extra data signals want.

        Mutates and returns the same dict. Each extra is best-effort; failures
        leave the key absent so signals degrade gracefully.
        """
        full = repo.get("full_name")
        if not full:
            return repo
        branch = repo.get("default_branch") or "main"

        readme = self.get_readme(full)
        if readme is not None:
            repo["readme"] = readme

        paths = self.get_tree(full, branch)
        if paths is not None:
            repo["file_paths"] = paths

        commits = self.get_commits_count(full)
        if commits is not None:
            repo["commits_count"] = commits

        contributors = self.get_contributors_count(full)
        if contributors is not None:
            repo["contributors_count"] = contributors

        # Sample a few source files for emoji-in-code detection.
        if paths:
            code_files = [p for p in paths if p.lower().endswith(_CODE_EXTS)]
            samples: List[str] = []
            for p in code_files[:sample_files]:
                content = self.get_file_content(full, p)
                if content:
                    samples.append(content[:20000])  # cap per-file size
            if samples:
                repo["code_samples"] = samples

        return repo

    def rate_limit_ok(self) -> bool:
        data = self._get_json("/rate_limit")
        if not data:
            return True  # don't block on an unknown state
        core = data.get("resources", {}).get("core", {})
        return core.get("remaining", 1) > 5
