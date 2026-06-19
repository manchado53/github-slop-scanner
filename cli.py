#!/usr/bin/env python3
"""GitHub Slop Scanner — CLI entry point.

Searches GitHub for low-effort 'AI slop' repos, scores them, and prints +
saves a ranked report.

Usage:
    python cli.py                                  # default query
    python cli.py --query "language:python stars:0..1 sort:updated" \\
                  --target 25 --min-score 60 --out results.json
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from slopscanner import report
from slopscanner.github import GitHubClient
from slopscanner.scanner import DEFAULT_QUERY, scan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slop-scanner",
        description="Scan GitHub for low-effort 'AI slop' repositories.",
    )
    p.add_argument("--query", default=DEFAULT_QUERY,
                   help="GitHub search query (default: recently-updated, near-zero-star repos).")
    p.add_argument("--target", type=int, default=25,
                   help="How many slop repos to collect before stopping (default 25).")
    p.add_argument("--min-score", type=int, default=60,
                   help="Minimum slop score (0-100) to count a repo (default 60).")
    p.add_argument("--max-pages", type=int, default=10,
                   help="Max search pages to fetch (default 10).")
    p.add_argument("--per-page", type=int, default=30,
                   help="Results per search page, max 100 (default 30).")
    p.add_argument("--out", default=None,
                   help="Base path for output files (writes <out>.json / .csv).")
    p.add_argument("--format", default="table",
                   help="Comma list of outputs: table,json,csv (default table).")
    p.add_argument("--quiet", action="store_true", help="Suppress progress lines.")
    p.add_argument("--verbose", action="store_true", help="Log GitHub API activity.")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("warning: no GITHUB_TOKEN set — limited to 60 requests/hour.\n"
              "         Set one in a .env file (see .env.example) for real scans.",
              file=sys.stderr)

    client = GitHubClient(token, verbose=args.verbose)

    def progress(msg: str) -> None:
        if not args.quiet:
            print(msg, file=sys.stderr)

    repos = scan(
        client,
        query=args.query,
        target=args.target,
        min_score=args.min_score,
        max_pages=args.max_pages,
        per_page=args.per_page,
        progress=progress,
    )

    formats = {f.strip().lower() for f in args.format.split(",") if f.strip()}

    if not repos:
        print("No repos matched the slop threshold. Try lowering --min-score "
              "or broadening --query.", file=sys.stderr)
        return 0

    if "table" in formats:
        report.print_table(repos)

    base = args.out or "results"
    if "json" in formats:
        report.write_json(repos, f"{base}.json")
        print(f"Wrote {base}.json", file=sys.stderr)
    if "csv" in formats:
        report.write_csv(repos, f"{base}.csv")
        print(f"Wrote {base}.csv", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
