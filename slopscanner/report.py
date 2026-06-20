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


def _score_color(score: int) -> str:
    return "red" if score >= 80 else "yellow" if score >= 60 else \
        "magenta" if score >= 40 else "green"


def print_table(repos: List[ScannedRepo]) -> None:
    """Compact, narrow-friendly ranked list (no wide table to squish).

    Each repo is one header line plus an indented 'why' line that wraps
    naturally on its own row, so it reads fine in any terminal width.
    """
    try:
        from rich.console import Console
    except ImportError:
        _print_plain(repos)
        return

    console = Console()
    width = max(2, len(str(len(repos))))
    console.print(f"\n[bold]GitHub Slop Scan[/bold] — {len(repos)} repos "
                  f"(sloppiest first)\n")

    for i, r in enumerate(repos, 1):
        color = _score_color(r.score)
        meta = f"★{r.stars}"
        if r.language:
            meta += f" · {r.language}"
        console.print(
            f"[dim]{i:>{width}}.[/dim] "
            f"[{color}]{r.score:>3}[/{color}] "
            f"[bold]{r.result.label():<10}[/bold] "
            f"[cyan]{r.full_name}[/cyan]  [dim]{meta}[/dim]"
        )
        if r.result.reasons:
            why = ", ".join(r.result.reasons[:5])
            console.print(f"[dim]{'':>{width}}     why:[/dim] {why}")
    console.print()


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
