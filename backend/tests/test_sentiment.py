import pytest

from app.etl.sentiment import classify_sentiment


def test_procedural_title_is_neutral_not_missing():
    assert classify_sentiment("Notice of Board Meeting") == pytest.approx(0.0)
    assert classify_sentiment("Transmission of Annual Report for the Year Ended 31 December 2025") == pytest.approx(
        0.0
    )


def test_positive_keyword_scores_positive():
    assert classify_sentiment("Company Reports Record Profit Growth") > 0


def test_negative_keyword_scores_negative():
    assert classify_sentiment("Suspension of RLNG Supply to Fertilizer Plant") < 0


def test_mixed_keywords_net_out():
    # one positive ("growth"), one negative ("decline") -> net zero
    assert classify_sentiment("Growth in Some Segments, Decline in Others") == pytest.approx(0.0)


def test_score_is_capped_at_plus_and_minus_one():
    very_negative = "Loss Default Suspension Closure Penalty Shortfall Delay Fraud"
    very_positive = "Profit Growth Increase Record Expansion Award Approval Recovery"
    assert classify_sentiment(very_negative) == pytest.approx(-1.0)
    assert classify_sentiment(very_positive) == pytest.approx(1.0)


def test_word_boundary_avoids_false_positive_substring_match():
    # "closed" should not match inside "enclosed" / "disclosed"-like words
    assert classify_sentiment("Disclosure of Material Information") == pytest.approx(0.0)


def test_book_closure_and_closed_period_are_not_negative():
    # PSX's own standard securities terms ("Book Closure" = share-transfer-book closing
    # period, "Closed Period" = insider-trading blackout window) -- routine and neutral,
    # not a facility shutdown. Regression test for a real false positive caught in the
    # 91-row production backfill on 2026-07-27.
    assert classify_sentiment("Board Meeting / Closed Period") == pytest.approx(0.0)
    assert classify_sentiment("Notice of Final Book Closure of FFBL Shares") == pytest.approx(0.0)
    # A genuine operational shutdown must still register as negative.
    assert classify_sentiment("Plant Shutdown Due to Gas Curtailment") < 0
