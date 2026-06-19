"""Unit tests for individual heuristic signals."""

from slopscanner import signals


def test_count_emoji():
    assert signals.count_emoji("plain text") == 0
    assert signals.count_emoji("ship it 🚀🔥") == 2
    assert signals.count_emoji("") == 0


def test_metadata_signals_fire_on_slop(slop_repo):
    assert signals.sig_zero_stars(slop_repo)[0] == 5.0
    assert signals.sig_zero_forks(slop_repo)[0] == 3.0
    assert signals.sig_no_description(slop_repo)[0] == 5.0
    assert signals.sig_no_license(slop_repo)[0] == 4.0
    assert signals.sig_default_name(slop_repo)[0] == 5.0
    assert signals.sig_brand_new(slop_repo)[0] == 3.0


def test_metadata_signals_silent_on_good(good_repo):
    assert signals.sig_zero_stars(good_repo)[0] == 0.0
    assert signals.sig_no_description(good_repo)[0] == 0.0
    assert signals.sig_no_license(good_repo)[0] == 0.0
    assert signals.sig_default_name(good_repo)[0] == 0.0


def test_readme_signals(slop_repo, good_repo):
    assert signals.sig_ai_boilerplate(slop_repo)[0] >= 7.0
    assert signals.sig_emoji_headers(slop_repo)[0] >= 3.0
    assert signals.sig_placeholder_text(slop_repo)[0] == 5.0
    assert signals.sig_readme_only(slop_repo)[0] == 4.0

    assert signals.sig_ai_boilerplate(good_repo)[0] == 0.0
    assert signals.sig_emoji_headers(good_repo)[0] == 0.0
    assert signals.sig_placeholder_text(good_repo)[0] == 0.0
    assert signals.sig_readme_only(good_repo)[0] == 0.0


def test_effort_signals(slop_repo, good_repo):
    assert signals.sig_single_commit(slop_repo)[0] == 8.0
    assert signals.sig_no_tests(slop_repo)[0] == 4.0
    assert signals.sig_no_ci(slop_repo)[0] == 4.0
    assert signals.sig_few_files(slop_repo)[0] == 4.0

    assert signals.sig_single_commit(good_repo)[0] == 0.0
    assert signals.sig_no_tests(good_repo)[0] == 0.0
    assert signals.sig_no_ci(good_repo)[0] == 0.0
    assert signals.sig_few_files(good_repo)[0] == 0.0


def test_activity_signals(slop_repo, good_repo):
    assert signals.sig_zero_issues(slop_repo)[0] == 4.0
    assert signals.sig_single_contributor(slop_repo)[0] == 4.0

    assert signals.sig_zero_issues(good_repo)[0] == 0.0
    assert signals.sig_single_contributor(good_repo)[0] == 0.0


def test_emoji_in_code(slop_repo, good_repo):
    pts, reason = signals.sig_emoji_in_code(slop_repo)
    assert pts > 0
    assert "emoji" in reason
    assert signals.sig_emoji_in_code(good_repo)[0] == 0.0


def test_signals_never_raise_on_empty():
    # An empty dict must never make a signal raise. Some "absence = slop"
    # signals (no stars, no license, ...) legitimately fire; we only require
    # that every signal returns a valid, bounded (points, reason) pair.
    empty = {}
    for sig, cap in signals.all_signals():
        points, reason = sig(empty)
        assert isinstance(points, float)
        assert 0.0 <= points <= cap
        assert reason is None or isinstance(reason, str)


def test_group_caps_sum_to_100():
    assert signals.MAX_RAW == 100.0
