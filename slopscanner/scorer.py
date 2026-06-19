"""Combine individual signals into a single 0-100 slop score.

The signal groups in :mod:`signals` are weighted so their caps already sum to
100 (metadata 25, readme 25, effort 20, activity 15, emoji-in-code 15). So the
score is simply the sum of awarded points, clamped to [0, 100]. Each scored
repo also carries the list of reasons and a per-group breakdown so the report
can explain *why* a repo looks like slop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from . import signals


@dataclass
class ScoreResult:
    score: int
    reasons: List[str] = field(default_factory=list)
    groups: Dict[str, float] = field(default_factory=dict)

    def label(self) -> str:
        if self.score >= 80:
            return "PRIME SLOP"
        if self.score >= 60:
            return "slop"
        if self.score >= 40:
            return "suspect"
        return "looks real"


def score(repo: dict) -> ScoreResult:
    """Score a (preferably enriched) repo dict. Returns a ScoreResult."""
    total = 0.0
    reasons: List[str] = []
    groups: Dict[str, float] = {}

    for group_name, entries in signals.GROUPS.items():
        group_points = 0.0
        for sig, cap in entries:
            try:
                points, reason = sig(repo)
            except Exception:
                # A misbehaving signal must never sink a whole scan.
                points, reason = 0.0, None
            points = max(0.0, min(points, cap))
            group_points += points
            if points > 0 and reason:
                reasons.append(reason)
        groups[group_name] = round(group_points, 1)
        total += group_points

    clamped = int(round(max(0.0, min(total, 100.0))))
    return ScoreResult(score=clamped, reasons=reasons, groups=groups)
