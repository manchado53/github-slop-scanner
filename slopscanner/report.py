"""Output: a ranked terminal table plus JSON / CSV dumps."""

from __future__ import annotations

import csv
import json
from typing import List

from .scanner import ScannedRepo


def to_records(repos: List[ScannedRepo]) -> List[dict]:
    return [
        {
            "rank": i + 1,
            "full_name": r.full_name,
            "url": r.html_url,
            "score": r.score,
            "label": r.result.label(),
            "stars": r.stars,
            "language": r.language,
            "description": r.description,
            "groups": r.result.groups,
            "reasons": r.result.reasons,
        }
        for i, r in enumerate(repos)
    ]


def write_json(repos: List[ScannedRepo], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_records(repos), f, indent=2, ensure_ascii=False)


def write_csv(repos: List[ScannedRepo], path: str) -> None:
    fields = ["rank", "full_name", "url", "score", "label", "stars",
              "language", "description", "reasons"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in to_records(repos):
            row = {k: rec.get(k) for k in fields}
            row["reasons"] = "; ".join(rec["reasons"])
            writer.writerow(row)


def print_table(repos: List[ScannedRepo]) -> None:
    """Pretty table via rich if available, else a plain-text fallback."""
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        _print_plain(repos)
        return

    console = Console()
    table = Table(title=f"GitHub Slop Scan — {len(repos)} repos", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("Repo", style="cyan", no_wrap=True)
    table.add_column("★", justify="right")
    table.add_column("Lang")
    table.add_column("Top reasons")

    for i, r in enumerate(repos):
        color = "red" if r.score >= 80 else "yellow" if r.score >= 60 else "white"
        reasons = ", ".join(r.result.reasons[:3])
        table.add_row(
            str(i + 1),
            f"[{color}]{r.score}[/{color}]",
            r.full_name,
            str(r.stars),
            r.language or "-",
            reasons,
        )
    console.print(table)


def print_detail(repo: ScannedRepo) -> None:
    """Full breakdown for a single repo: score, per-group points, every reason."""
    r = repo.result
    print()
    print(f"{repo.full_name}   {repo.html_url}")
    print(f"  score: {r.score}/100   ->  {r.label()}")
    print(f"  stars: {repo.stars}   language: {repo.language or '-'}")
    if repo.description:
        print(f"  about: {repo.description}")
    print("  group breakdown:")
    for group, pts in r.groups.items():
        print(f"    {group:<11} {pts:>5}")
    print("  reasons:")
    if r.reasons:
        for reason in r.reasons:
            print(f"    - {reason}")
    else:
        print("    (none — this repo shows no slop tells)")
    print()


def _print_plain(repos: List[ScannedRepo]) -> None:
    print(f"\nGitHub Slop Scan — {len(repos)} repos\n" + "=" * 60)
    for i, r in enumerate(repos):
        print(f"{i + 1:>3}. [{r.score:>3}] {r.full_name}  (★{r.stars}, {r.language or '-'})")
        print(f"     {r.html_url}")
        if r.result.reasons:
            print(f"     why: {', '.join(r.result.reasons[:4])}")
