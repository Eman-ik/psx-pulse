"""Statement parsing and gap handling. The fixture is the text of FFC's own condensed interim standalone
statement of financial position (pages 11-12 of the half-year report filed on PSX, 2026-08-27)."""

from datetime import date

import pytest

from app.ingestion.filing_statements import TieOutError, parse_balance_sheet
from app.research_system import research_view as rv

PAGE_11 = 'CONDENSED INTERIM STATEMENT OF FINANCIAL POSITION\nAs at June 30, 2026\nUn-audited Audited\nJune 30, December 31,\nNote 2026 2025\n(Rupees ‘000)\nEQUITY AND LIABILITIES\nEQUITY AND RESERVES\nShare capital 4 14,390,232 14,231,086\nCapital reserves 28,000,080 28,000,080\nRevenue reserves\nGeneral reserves 8,802,360 8,802,360\nUnappropriated profit 101,878,995 84,496,584\n110,681,355 93,298,944\nSurplus on remeasurement of investments\nto fair value - net 49,806 53,415\n153,121,473 135,583,525\nNON - CURRENT LIABILITIES\nLong term borrowings - secured 5 72,375,000 50,250,000\nDeferred tax liability 8,392,875 7,911,767\nCompensated leave absences 950,000 3,044,643\n81,717,875 61,206,410\nCURRENT LIABILITIES\nCurrent portion of long term borrowings - secured 5 13,400,000 11,050,000\nTrade and other payables 6 213,147,480 194,053,067\nMark-up and profit accrued 833,440 940,275\nShort term borrowings - secured 7 18,448,354 18,594,647\nUnclaimed dividend 862,749 850,812\nProvision for taxation 11,194,496 15,206,397\n257,886,519 240,695,198\nTOTAL LIABILITIES 339,604,394 301,901,608\nTOTAL EQUITY AND LIABILITIES 492,725,867 437,485,133\nCONTINGENCIES AND COMMITMENTS 8\nThe annexed notes 1 to 22 form an integral part of these condensed interim financial statements.\n10'
PAGE_12 = 'Half Yearly Financial Statements 2026\nCONDENSED INTERIM STATEMENT OF FINANCIAL POSITION\nAs at June 30, 2026\nUn-audited Audited\nJune 30, December 31,\nNote 2026 2025\n(Rupees ‘000)\nASSETS\nNON - CURRENT ASSETS\nProperty, plant and equipment 9 96,574,989 76,550,175\nIntangible assets 1,701,758 1,591,378\nLong term investments 10 109,835,268 79,070,285\nLong term loans and advances - secured 5,876,587 4,529,993\nLong term deposits and prepayments 91,021 91,021\n214,079,623 161,832,852\nCURRENT ASSETS\nStores, spares and loose tools 15,826,295 15,566,472\nStock in trade 64,425,128 38,229,377\nTrade debts 1,493,943 20,153,212\nLoans and advances - secured 7,386,611 5,682,181\nDeposits and prepayments 503,944 1,058,747\nOther receivables 11 9,627,409 5,163,143\nShort term investments 12 174,360,789 181,455,741\nCash and bank balances 5,022,125 8,343,408\n278,646,244 275,652,281\nTOTAL ASSETS 492,725,867 437,485,133\nChairman Chief Executive Officer Director Chief Financial Officer\n11'


def test_dec_2025_balance_sheet_is_read_from_the_audited_column_and_ties_out():
    f = parse_balance_sheet([PAGE_11, PAGE_12])
    assert f["total_assets"]["value"] == 437_485_133
    assert f["total_liabilities"]["value"] == 301_901_608
    assert f["total_equity"]["value"] == 135_583_525  # unlabelled subtotal in the statement
    assert f["current_assets"]["value"] == 275_652_281 and f["current_liabilities"]["value"] == 240_695_198
    assert f["inventory"]["value"] == 38_229_377 and f["trade_debts"]["value"] == 20_153_212
    assert f["total_assets"]["current"] == 492_725_867  # the interim (June 2026) column is kept separate


def test_a_balance_sheet_that_does_not_tie_is_rejected_not_stored():
    broken = PAGE_12.replace("TOTAL ASSETS 492,725,867 437,485,133", "TOTAL ASSETS 492,725,867 437,485,134")
    with pytest.raises(TieOutError, match="total assets"):
        parse_balance_sheet([PAGE_11, broken])


def test_a_subtotal_that_is_not_the_sum_of_its_rows_is_rejected():
    broken = PAGE_12.replace("Trade debts 1,493,943 20,153,212", "Trade debts 1,493,943 20,153,213")
    with pytest.raises(TieOutError, match="current assets"):
        parse_balance_sheet([PAGE_11, broken])


def test_consolidated_pages_are_refused():
    with pytest.raises(TieOutError, match="standalone"):
        parse_balance_sheet([PAGE_11.replace("CONDENSED INTERIM STATEMENT", "CONDENSED INTERIM CONSOLIDATED STATEMENT"), PAGE_12])


def _series(*pairs):
    return [(date(y, 12, 31), v) for y, v in pairs]


def test_research_view_does_not_compare_years_across_a_gap():
    ratios = {k: _series((2022, 1), (2023, 2), (2025, 3)) for k in ("net_profit_margin", "roe", "debt_to_equity", "current_ratio")}
    assert rv.financial_health(ratios, date(2026, 10, 2))["state"] == "INSUFFICIENT_DATA"


def test_research_view_uses_only_signals_from_the_latest_year():
    ratios = {
        "net_profit_margin": _series((2024, 17.3), (2025, 17.0)),
        "roe": _series((2022, 40), (2023, 54)),  # older era, must be ignored
        "debt_to_equity": _series((2024, 3.0), (2025, 2.2)),
        "current_ratio": _series((2024, 1.0), (2025, 1.1)),
    }
    d = rv.financial_health(ratios, date(2026, 6, 1))
    assert d["state"] != "INSUFFICIENT_DATA" and len(d["inputs"]) == 3 and all(i["period_end"].startswith("2025") for i in d["inputs"])
