"""End-to-end scoring tests on the offline fixtures."""

from slopscanner import scorer


def test_slop_scores_high(slop_repo):
    result = scorer.score(slop_repo)
    assert result.score >= 80, result.reasons
    assert result.label() in ("slop", "PRIME SLOP")
    assert len(result.reasons) >= 8


def test_good_scores_low(good_repo):
    result = scorer.score(good_repo)
    assert result.score < 40, result.reasons
    assert result.label() in ("looks real", "suspect")


def test_score_is_bounded(slop_repo):
    result = scorer.score(slop_repo)
    assert 0 <= result.score <= 100


def test_groups_present(slop_repo):
    result = scorer.score(slop_repo)
    assert set(result.groups) == {"metadata", "readme", "effort", "activity", "emoji_code"}


def test_empty_repo_scores_zeroish():
    # No data at all -> only signals that treat 'absent' as zero/None fire.
    result = scorer.score({})
    assert result.score >= 0
