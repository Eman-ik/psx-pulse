from app.research_system.screening_funnel import ScreeningFunnel


def test_missing_peer_percentiles_are_not_scored_as_median():
    passes, composite, _ = ScreeningFunnel.screen_4_peer_comparison({}, {"roe_percentile": 10})
    assert composite == 10 and passes is False


def test_tradable_company_without_statements_is_not_evaluated_not_passed():
    passes, reasons = ScreeningFunnel.screen_1_basic_quality(
        {}, is_active=True, has_recent_prices=True, balance_sheet_health={"debt_to_equity": None, "current_ratio": None}
    )
    assert passes is None and "not run" in reasons[0]
    assert ScreeningFunnel.screen_1_basic_quality({}, is_active=True, has_recent_prices=False)[0] is False


def test_valuation_without_sector_comparison_is_not_evaluated():
    passes, score, _ = ScreeningFunnel.screen_3_valuation({}, {"pe_ratio": 8.0, "pe_sector_median": None})
    assert passes is None and score == 0.0


def test_no_peer_percentiles_means_no_verdict():
    assert ScreeningFunnel.screen_4_peer_comparison({}, {"unrelated": 1}) == (None, 0.0, ["No peer percentiles available"])
