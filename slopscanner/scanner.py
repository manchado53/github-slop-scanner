"""The scan loop: page through GitHub search, enrich + score each repo, and
keep going until enough high-scoring slop repos are collected (or limits hit).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from .github import GitHubClient, RateLimitError
from .scorer import ScoreResult, score


@dataclass
class ScannedRepo:
    full_name: str
    html_url: str
    description: str
    stars: int
    language: Optional[str]
    result: ScoreResult

    @property
    def score(self) -> int:
        return self.result.score


# Recently-created repos are the richest hunting ground for one-shot AI dumps.
DEFAULT_QUERY = "stars:0..2 size:<2000 sort:updated"


def scan(
    client: GitHubClient,
    query: str = DEFAULT_QUERY,
    *,
    target: int = 25,
    min_score: int = 60,
    max_pages: int = 10,
    per_page: int = 30,
    progress: Optional[Callable[[str], None]] = None,
) -> List[ScannedRepo]:
    """Collect up to ``target`` repos scoring >= ``min_score``.

    Loops over search pages until the target is met, the page budget is spent,
    or the rate limit forces a stop. Returns repos sorted by score (desc).
    """
    def emit(msg: str) -> None:
        if progress:
            progress(msg)

    collected: List[ScannedRepo] = []
    page = 1

    while len(collected) < target and page <= max_pages:
        if not client.rate_limit_ok():
            emit("Rate limit nearly exhausted — stopping early.")
            break

        emit(f"Fetching page {page} (have {len(collected)}/{target} slop repos)…")
        try:
            items = client.search_repos(query, page=page, per_page=per_page)
        except RateLimitError as exc:
            emit(f"Stopped: {exc}")
            break

        if not items:
            emit("No more results.")
            break

        for repo in items:
            try:
                client.enrich(repo)
            except RateLimitError as exc:
                emit(f"Stopped during enrichment: {exc}")
                items = []
                break
            res = score(repo)
            if res.score >= min_score:
                collected.append(
                    ScannedRepo(
                        full_name=repo.get("full_name", "?"),
                        html_url=repo.get("html_url", ""),
                        description=(repo.get("description") or "").strip(),
                        stars=repo.get("stargazers_count", 0),
                        language=repo.get("language"),
                        result=res,
                    )
                )
                emit(f"  + {repo.get('full_name')} scored {res.score} ({res.label()})")
                if len(collected) >= target:
                    break

        page += 1

    collected.sort(key=lambda r: r.score, reverse=True)
    return collected


def scan_user(
    client: GitHubClient,
    username: str,
    *,
    min_score: int = 0,
    max_repos: int = 300,
    include_forks: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> List[ScannedRepo]:
    """Score every public repo a user owns and return them sorted by score.

    Unlike :func:`scan`, this is an audit of one account: it does not stop at a
    target and ``min_score`` defaults to 0 so you see the full report card.
    """
    def emit(msg: str) -> None:
        if progress:
            progress(msg)

    emit(f"Listing repos for '{username}'…")
    repos = client.list_user_repos(username, include_forks=include_forks,
                                   max_repos=max_repos)
    if not repos:
        emit(f"No public repos found for '{username}' (or user/org does not exist).")
        return []
    emit(f"Found {len(repos)} repos — scoring each…")

    scanned: List[ScannedRepo] = []
    for i, repo in enumerate(repos, 1):
        if not client.rate_limit_ok():
            emit("Rate limit nearly exhausted — stopping early.")
            break
        try:
            client.enrich(repo)
        except RateLimitError as exc:
            emit(f"Stopped during enrichment: {exc}")
            break
        res = score(repo)
        if res.score >= min_score:
            scanned.append(
                ScannedRepo(
                    full_name=repo.get("full_name", "?"),
                    html_url=repo.get("html_url", ""),
                    description=(repo.get("description") or "").strip(),
                    stars=repo.get("stargazers_count", 0),
                    language=repo.get("language"),
                    result=res,
                )
            )
        emit(f"  [{i}/{len(repos)}] {repo.get('full_name')} -> {res.score} ({res.label()})")

    scanned.sort(key=lambda r: r.score, reverse=True)
    return scanned
