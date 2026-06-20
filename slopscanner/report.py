"""Output: a ranked terminal table plus JSON / CSV / HTML dumps."""

from __future__ import annotations

import csv
import html
import json
from typing import Dict, List

from .scanner import ScannedRepo


def summarize(repos: List[ScannedRepo]) -> Dict:
    """Counts + averages for a set of scored repos (used by HTML + summaries)."""
    n = len(repos)
    scores = [r.score for r in repos]
    buckets = {"prime": 0, "slop": 0, "suspect": 0, "real": 0}
    for s in scores:
        if s >= 80:
            buckets["prime"] += 1
        elif s >= 60:
            buckets["slop"] += 1
        elif s >= 40:
            buckets["suspect"] += 1
        else:
            buckets["real"] += 1
    return {
        "count": n,
        "avg": round(sum(scores) / n, 1) if n else 0,
        "max": max(scores) if scores else 0,
        "min": min(scores) if scores else 0,
        "buckets": buckets,
    }


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


_HTML_TIER = [
    (80, "prime", "PRIME SLOP", "#ef4444"),
    (60, "slop", "slop", "#f59e0b"),
    (40, "suspect", "suspect", "#a855f7"),
    (0, "real", "looks real", "#22c55e"),
]


def _tier(score: int):
    for lo, cls, label, color in _HTML_TIER:
        if score >= lo:
            return cls, label, color
    return "real", "looks real", "#22c55e"


def write_html(repos: List[ScannedRepo], path: str, title: str = "GitHub Slop Scan") -> None:
    """Write a self-contained HTML report (no external assets) you can open
    in any browser."""
    s = summarize(repos)
    e = html.escape

    cards = []
    for i, r in enumerate(repos, 1):
        cls, label, color = _tier(r.score)
        chips = "".join(
            f'<span class="chip">{e(reason)}</span>' for reason in r.result.reasons
        )
        groups = "".join(
            f'<span class="grp"><b>{e(g)}</b> {pts}</span>'
            for g, pts in r.result.groups.items()
        )
        desc = f'<div class="desc">{e(r.description)}</div>' if r.description else ""
        cards.append(f"""
    <article class="card {cls}">
      <div class="rank">#{i}</div>
      <div class="badge" style="--c:{color}">{r.score}<small>/100</small></div>
      <div class="body">
        <div class="head">
          <a href="{e(r.html_url)}" target="_blank" rel="noopener">{e(r.full_name)}</a>
          <span class="label" style="color:{color}">{e(label)}</span>
        </div>
        <div class="meta">★ {r.stars} &nbsp;·&nbsp; {e(r.language or "—")}</div>
        {desc}
        <div class="groups">{groups}</div>
        <div class="chips">{chips}</div>
      </div>
    </article>""")

    b = s["buckets"]
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#0b0e14; color:#e6e9ef;
         font:15px/1.5 ui-sans-serif,system-ui,Segoe UI,Roboto,Arial; }}
  .wrap {{ max-width: 920px; margin: 0 auto; padding: 32px 20px 64px; }}
  h1 {{ font-size: 24px; margin: 0 0 4px; }}
  .sub {{ color:#8b93a7; margin-bottom: 24px; }}
  .summary {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom: 28px; }}
  .stat {{ background:#141925; border:1px solid #222a3a; border-radius:12px;
           padding:12px 16px; min-width:110px; }}
  .stat .n {{ font-size:22px; font-weight:700; }}
  .stat .k {{ color:#8b93a7; font-size:12px; text-transform:uppercase;
              letter-spacing:.04em; }}
  .card {{ display:grid; grid-template-columns:44px 86px 1fr; gap:14px;
           align-items:start; background:#141925; border:1px solid #222a3a;
           border-left:4px solid #2a3346; border-radius:14px; padding:16px;
           margin-bottom:12px; }}
  .card.prime {{ border-left-color:#ef4444; }}
  .card.slop {{ border-left-color:#f59e0b; }}
  .card.suspect {{ border-left-color:#a855f7; }}
  .card.real {{ border-left-color:#22c55e; }}
  .rank {{ color:#5b647a; font-weight:700; padding-top:8px; }}
  .badge {{ background:color-mix(in srgb, var(--c) 18%, #141925);
            border:1px solid var(--c); color:var(--c); border-radius:10px;
            text-align:center; padding:10px 0; font-size:24px; font-weight:800; }}
  .badge small {{ font-size:11px; font-weight:600; opacity:.7; }}
  .head {{ display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }}
  .head a {{ color:#7dd3fc; text-decoration:none; font-weight:600;
             font-size:16px; word-break:break-all; }}
  .head a:hover {{ text-decoration:underline; }}
  .label {{ font-size:12px; font-weight:700; text-transform:uppercase;
            letter-spacing:.04em; }}
  .meta {{ color:#8b93a7; font-size:13px; margin:2px 0 6px; }}
  .desc {{ color:#c3c9d6; margin-bottom:8px; }}
  .groups {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }}
  .grp {{ font-size:11px; color:#9aa3b6; background:#0f131c;
          border:1px solid #222a3a; border-radius:6px; padding:2px 7px; }}
  .grp b {{ color:#cdd3e0; font-weight:600; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .chip {{ font-size:12px; background:#1d2433; border:1px solid #2b3446;
           color:#cdd3e0; border-radius:999px; padding:3px 10px; }}
  footer {{ color:#5b647a; font-size:12px; margin-top:24px; text-align:center; }}
</style></head>
<body><div class="wrap">
  <h1>{e(title)}</h1>
  <div class="sub">{s['count']} repos · sloppiest first · higher score = more slop</div>
  <div class="summary">
    <div class="stat"><div class="n">{s['count']}</div><div class="k">repos</div></div>
    <div class="stat"><div class="n">{s['avg']}</div><div class="k">avg score</div></div>
    <div class="stat"><div class="n" style="color:#ef4444">{b['prime']}</div><div class="k">prime slop</div></div>
    <div class="stat"><div class="n" style="color:#f59e0b">{b['slop']}</div><div class="k">slop</div></div>
    <div class="stat"><div class="n" style="color:#a855f7">{b['suspect']}</div><div class="k">suspect</div></div>
    <div class="stat"><div class="n" style="color:#22c55e">{b['real']}</div><div class="k">looks real</div></div>
  </div>
  {"".join(cards)}
  <footer>Generated by github-slop-scanner · heuristics, not proof.</footer>
</div></body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


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
