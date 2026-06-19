"""Shared offline fixtures: one obvious slop repo, one obviously real repo."""

from datetime import datetime, timedelta, timezone

import pytest

_SLOP_README = """\
# 🚀 My Project 🚀
## ✨ Features ✨
## 🔥 Installation
As an AI language model, I have created this comprehensive project for you.
In conclusion, this project will revolutionize the way you work.
TODO: add real content here
lorem ipsum dolor sit amet
"""

_GOOD_README = """\
# fastquery

A small, well-tested HTTP client for talking to JSON APIs.

## Installation

    pip install fastquery

## Usage

See the docs at https://example.com/fastquery for the full API. Contributions
welcome — please read CONTRIBUTING.md and open an issue before large changes.
"""


@pytest.fixture
def slop_repo():
    day = "2026-06-18T10:00:00Z"
    return {
        "name": "my-project",
        "full_name": "someuser/my-project",
        "html_url": "https://github.com/someuser/my-project",
        "description": "",
        "stargazers_count": 0,
        "forks_count": 0,
        "license": None,
        "open_issues_count": 0,
        "language": "Python",
        "default_branch": "main",
        "created_at": day,
        "pushed_at": day,
        "updated_at": day,
        # enriched extras
        "readme": _SLOP_README,
        "file_paths": ["README.md"],
        "commits_count": 1,
        "contributors_count": 1,
        "code_samples": ["def go():\n    print('launching 🚀')  # ship it 🔥\n"],
    }


@pytest.fixture
def good_repo():
    recent = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    old = "2019-01-05T08:00:00Z"
    return {
        "name": "fastquery",
        "full_name": "acme/fastquery",
        "html_url": "https://github.com/acme/fastquery",
        "description": "A small, well-tested HTTP client for JSON APIs.",
        "stargazers_count": 4200,
        "forks_count": 310,
        "license": {"key": "mit", "name": "MIT License"},
        "open_issues_count": 47,
        "language": "Python",
        "default_branch": "main",
        "created_at": old,
        "pushed_at": recent,
        "updated_at": recent,
        "readme": _GOOD_README,
        "file_paths": [
            "src/fastquery/__init__.py",
            "src/fastquery/client.py",
            "src/fastquery/auth.py",
            "tests/test_client.py",
            "tests/test_auth.py",
            ".github/workflows/ci.yml",
            "README.md",
            "LICENSE",
        ],
        "commits_count": 612,
        "contributors_count": 23,
        "code_samples": [
            "def get(url):\n    return _request('GET', url)\n",
            "class Client:\n    def __init__(self, base):\n        self.base = base\n",
        ],
    }
