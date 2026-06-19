# GitHub Slop Scanner — Plan

## What
A Python CLI tool that searches GitHub for repositories that look like low-effort
"AI slop" — repos with little real thought or work behind them — and ranks them by a
slop score.

## Why
Lots of repos are generated in one shot by AI, pushed once, and abandoned. They share
tells: generic AI README, emoji-stuffed everything, one giant commit, no tests, no
issues, no users. This tool finds and scores those tells so you can see them at a glance.

## How (high level)
1. **Fetch** repos from the GitHub Search API (token-authenticated, 5000 req/hr).
   Caller gives a search query (e.g. recently created repos in a language).
2. **Score** each repo with weighted heuristics across five signal groups:
   - Repo metadata — no stars, 1-2 commits, no description/license, default name.
   - README quality — AI boilerplate phrases, emoji-stuffed headers, placeholder text.
   - Code/commit effort — single commit, no tests, no CI, tiny code.
   - Activity — no issues, no PRs, only the owner, abandoned after creation.
   - Emojis in code — emoji found inside source files, not just the README.
3. **Report** results: ranked table in the terminal + a JSON/CSV dump, with per-repo
   reasons for the score ("why it scored slop").

## The "loop"
A run keeps scanning pages of results and accumulating scored repos until it has
collected a target number of high-scoring slop repos (or hits the API/page limit),
so one invocation reliably produces a finished list.

## Shape
```
github-slop-scanner/
  slopscanner/
    __init__.py
    github.py      # API client (search, repo details, readme, contents)
    signals.py     # individual heuristic checks -> partial scores + reasons
    scorer.py      # combine signals into a 0-100 slop score
    scanner.py     # the scan loop (fetch pages until N slop repos found)
    report.py      # terminal table + JSON/CSV output
  cli.py           # entry point / arg parsing
  tests/           # unit tests for signals + scorer (offline, fixture-based)
  requirements.txt
  README.md
  .env.example     # GITHUB_TOKEN=...
```

## Config / secrets
- `GITHUB_TOKEN` read from env (or `.env`). Never committed; `.env` is gitignored.

## Out of scope (for now)
- Web dashboard, database, scheduled runs. Can come later.
