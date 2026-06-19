# GitHub Slop Scanner

Find GitHub repositories that look like low-effort **"AI slop"** — repos generated in one
shot, pushed once, and abandoned, with little real thought behind them. The scanner
searches GitHub, scores each repo on a set of slop "tells," and prints a ranked report
explaining *why* each repo scored the way it did.

## What counts as slop?

Each repo gets a **0–100 slop score** built from five signal groups (caps shown):

| Group | Max | Looks at |
|-------|-----|----------|
| Repo metadata | 25 | 0 stars/forks, no description, no license, low-effort name, created-and-abandoned same day |
| README quality | 25 | AI-boilerplate phrasing, emoji-stuffed headers, placeholder text, README-but-no-code |
| Code / commit effort | 20 | single commit, no tests, no CI, only a file or two |
| Activity | 15 | no issues/PRs, single contributor, no pushes after creation, long abandoned |
| Emojis in code | 15 | emoji found inside actual source files (a strong AI tell) |

Higher score = sloppier. 80+ is labeled **PRIME SLOP**, 60+ **slop**, 40+ **suspect**.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then put your GitHub token in .env
```

Create a token at <https://github.com/settings/tokens> (no scopes needed for public
repos). Without a token you're limited to 60 requests/hour.

## Usage

Two modes:

**1. Hunt mode** — search GitHub broadly for slop:

```bash
# Default: hunt recently-updated, near-zero-star repos
python cli.py

# Custom query + outputs
python cli.py --query "language:python stars:0..1 sort:updated" \
              --target 25 --min-score 60 \
              --out results --format table,json,csv
```

**2. Audit mode** — score *every* public repo a single user/org owns:

```bash
python cli.py --user some-username
python cli.py --user some-username --include-forks --out report
```

In audit mode the scanner pulls all of that account's repos, scores each, and shows the
full list (sloppiest first). `--min-score` defaults to 0 here so nothing is hidden;
forks are skipped unless you pass `--include-forks`.

Key flags:

- `--query` — any [GitHub search query](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories).
- `--target` — how many slop repos to collect before stopping (the scan loops over pages until it hits this).
- `--min-score` — minimum score (0–100) for a repo to count.
- `--max-pages`, `--per-page` — bound the search.
- `--format` — any of `table,json,csv`.
- `--out` — base path for `<out>.json` / `<out>.csv`.

## How the loop works

One run keeps fetching pages of search results, enriching and scoring each repo, and
collecting the ones above the threshold — until it has `--target` slop repos, runs out of
pages, or the rate limit forces a clean stop. So a single invocation reliably produces a
finished, ranked list.

## Tests

```bash
python -m pytest tests/
```

The tests are fully offline (fixture-based): a known-slop sample must score high and a
known-good sample must score low. No network or token required.

## Layout

```
slopscanner/
  github.py    # GitHub REST client (search, readme, tree, counts, file samples)
  signals.py   # one pure function per heuristic -> (points, reason)
  scorer.py    # combine signals -> 0-100 score + reasons + group breakdown
  scanner.py   # the page-by-page scan loop
  report.py    # rich terminal table + JSON/CSV writers
cli.py         # entry point
tests/         # offline fixture tests
```

## Caveats

Heuristics, not proof. A high score means a repo *looks* low-effort; it isn't a judgment
of any person. Tune the weights in `slopscanner/signals.py` (`GROUPS`) to taste.
