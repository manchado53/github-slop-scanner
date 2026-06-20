"""Generate a demo HTML report from synthetic data (no real repos/people).

Used to produce the screenshot in the README. Run:  python tools/make_demo_report.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slopscanner import report
from slopscanner.scanner import ScannedRepo
from slopscanner.scorer import ScoreResult

# Invented repos that illustrate each tier. Any resemblance is coincidental.
DEMO = [
    ScannedRepo(
        "exampledev/ultimate-ai-todo-app", "https://github.com/exampledev/ultimate-ai-todo-app",
        "🚀 The ULTIMATE todo app powered by AI ✨", 0, "JavaScript",
        ScoreResult(88, [
            "0 stars", "0 forks", "no license", "low-effort name",
            'AI-boilerplate phrasing ("unleash the power")',
            "8 of 9 headers stuffed with emoji", "placeholder text ('coming soon')",
            "single commit (one-shot dump)", "no tests", "no CI configuration",
            "12 emoji inside code across 3 file(s)",
        ], {"metadata": 22.0, "readme": 25.0, "effort": 16.0, "activity": 11.0, "emoji_code": 14.0})),
    ScannedRepo(
        "exampledev/crypto-trading-bot-2024", "https://github.com/exampledev/crypto-trading-bot-2024",
        "", 0, "Python",
        ScoreResult(71, [
            "0 stars", "no description", "no license",
            "created and last pushed within one day", "single commit (one-shot dump)",
            "no tests", "no open issues/PRs", "only the owner ever contributed",
            "5 emoji inside code across 2 file(s)",
        ], {"metadata": 20.0, "readme": 9.0, "effort": 16.0, "activity": 11.0, "emoji_code": 15.0})),
    ScannedRepo(
        "exampledev/my-portfolio-site", "https://github.com/exampledev/my-portfolio-site",
        "personal portfolio", 1, "HTML",
        ScoreResult(52, [
            "0 forks", "no license", "created and last pushed within one day",
            "README but essentially no code", "no tests", "no CI configuration",
            "no open issues/PRs",
        ], {"metadata": 12.0, "readme": 9.0, "effort": 12.0, "activity": 8.0, "emoji_code": 11.0})),
    ScannedRepo(
        "exampledev/weather-cli", "https://github.com/exampledev/weather-cli",
        "Tiny command-line weather tool with tests and CI.", 3, "Go",
        ScoreResult(31, [
            "0 forks", "no license", "only 3 commits",
        ], {"metadata": 12.0, "readme": 0.0, "effort": 12.0, "activity": 7.0, "emoji_code": 0.0})),
    ScannedRepo(
        "openhq/fastquery", "https://github.com/openhq/fastquery",
        "A small, well-tested HTTP client for JSON APIs.", 4200, "Python",
        ScoreResult(8, [
            "no open issues/PRs",
        ], {"metadata": 0.0, "readme": 0.0, "effort": 0.0, "activity": 8.0, "emoji_code": 0.0})),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "demo_report.html")
    report.write_html(DEMO, out, title="Slop scan: exampledev (demo)")
    print(out)
