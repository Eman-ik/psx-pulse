"""Tests for app/universe.py -- the fertilizer/cement universe and its guard rails.

These pin down the failures that are silent in production rather than loud:

1. Ex-marker normalization. PSX returns LUCKXD on Lucky Cement's ex-dividend date. Ingest
   that raw and you mint a phantom Security that never matches LUCK's fundamentals, and
   nothing errors -- you just get a company page that is permanently empty.

2. Instrument filtering. Preference shares and rights lines carry their own symbols. Left in,
   they appear as extra "companies" whose ratios are nonsense.

3. Tier assignment. The unverified cement figures must never be classified as renderable.
   A regression here puts unchecked balance-sheet numbers in front of a user behind a UI
   that looks exactly as confident as the verified ones -- and with scope cut to these two
   sectors, that is 10 of the 18 cement names.
"""

import pytest

from app.universe import (
    KNOWN_INACTIVE,
    TIER_FULL,
    TIER_PRICE_ONLY,
    TIER_UNVERIFIED,
    UNVERIFIED_FUNDAMENTALS,
    VERIFIED_FUNDAMENTALS,
    UniverseEntry,
    coverage_tier,
    is_common_equity,
    normalize_symbol,
    tier_counts,
)

# The psxdata.symbols() master list never contains ex-marker forms -- that is the whole
# basis for the normalization rule, so the fixture has to reflect it.
KNOWN = {"LUCK", "BOP", "COLG", "AICL", "LCI", "SAZEW", "FFC", "EFERT", "MAXD"}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("LUCKXD", "LUCK"), ("BOPXD", "BOP"), ("COLGXD", "COLG"), ("LCIXD", "LCI")],
)
def test_strips_ex_marker_when_base_symbol_is_real(raw, expected):
    assert normalize_symbol(raw, KNOWN) == expected


def test_leaves_plain_symbols_alone():
    assert normalize_symbol("FFC", KNOWN) == "FFC"
    assert normalize_symbol("EFERT", KNOWN) == "EFERT"


def test_does_not_strip_a_real_symbol_that_merely_ends_in_xd():
    """MAXD is in the master list, so it is a ticker, not MA on its ex-dividend date.

    This is the case that makes the rule conditional instead of a blind rstrip.
    """
    assert normalize_symbol("MAXD", KNOWN) == "MAXD"


def test_normalizes_case_and_whitespace():
    assert normalize_symbol("  luckxd  ", KNOWN) == "LUCK"


def test_without_a_master_list_falls_back_to_suffix_stripping():
    """Degraded mode when symbols() is unreachable. Looser, and knowingly so."""
    assert normalize_symbol("LUCKXD", None) == "LUCK"
    assert normalize_symbol("MAXD", None) == "MA"  # the false positive we accept when blind


def test_does_not_strip_when_stripping_empties_the_symbol():
    assert normalize_symbol("XD", KNOWN) == "XD"


@pytest.mark.parametrize("symbol", ["AGLNCPS", "POWERPS", "FLYNGR1", "JVDCR1"])
def test_preference_and_rights_lines_are_not_common_equity(symbol):
    assert not is_common_equity(symbol)


@pytest.mark.parametrize("symbol", ["FFC", "LUCK", "DGKC", "AGL", "AHCL", "THCCL"])
def test_ordinary_tickers_are_common_equity(symbol):
    assert is_common_equity(symbol)


def test_known_inactive_entries_all_carry_a_reason():
    """A bare symbol set would let "no price data" and "dead company" blur together."""
    assert KNOWN_INACTIVE
    for symbol, reason in KNOWN_INACTIVE.items():
        assert reason.strip(), f"{symbol} is excluded with no stated reason"


def test_engro_and_ffbl_are_excluded_as_stale_records():
    """Both still appear under FERTILIZER in symbols() but return zero price bars."""
    assert "ENGRO" in KNOWN_INACTIVE
    assert "FFBL" in KNOWN_INACTIVE


def test_verified_fertilizer_symbols_are_renderable():
    for symbol in ("FFC", "EFERT", "FATIMA"):
        assert coverage_tier(symbol) == TIER_FULL


def test_unverified_cement_symbols_are_quarantined():
    """The cement seed's own header says its figures were never checked against the PDFs."""
    for symbol in ("LUCK", "DGKC", "MLCF", "FCCL", "KOHC", "CHCC", "BWCL", "ACPL", "DCL", "GWLC"):
        assert coverage_tier(symbol) == TIER_UNVERIFIED


def test_uncovered_sector_members_are_price_only():
    """Live cement/fertilizer names nobody has entered financials for yet."""
    for symbol in ("AGL", "AHCL", "THCCL", "PIOC", "POWER", "FECTC"):
        assert coverage_tier(symbol) == TIER_PRICE_ONLY


def test_javedan_preference_is_not_treated_as_a_cement_company():
    """PSX classifies Javedan under PROPERTY, so JVDCPS never enters this universe.

    It was previously carried in the cement seed file, which is why this is worth asserting
    rather than assuming.
    """
    assert "JVDCPS" not in UNVERIFIED_FUNDAMENTALS
    assert "JVDCPS" not in VERIFIED_FUNDAMENTALS
    assert not is_common_equity("JVDCPS")


def test_verified_and_unverified_sets_are_disjoint():
    """A symbol in both sets would resolve to FULL and silently escape quarantine."""
    assert not (VERIFIED_FUNDAMENTALS & UNVERIFIED_FUNDAMENTALS)


def _entry(symbol: str, tier: str, sector: str = "CEMENT") -> UniverseEntry:
    return UniverseEntry(symbol=symbol, name=symbol, sector=sector, coverage_tier=tier)


def test_only_full_tier_entries_are_renderable():
    assert _entry("FFC", TIER_FULL, "FERTILIZER").has_renderable_fundamentals
    assert not _entry("LUCK", TIER_UNVERIFIED).has_renderable_fundamentals
    assert not _entry("THCCL", TIER_PRICE_ONLY).has_renderable_fundamentals


def test_tier_counts_covers_every_tier_even_when_empty():
    counts = tier_counts([_entry("FFC", TIER_FULL, "FERTILIZER")])
    assert counts == {TIER_FULL: 1, TIER_UNVERIFIED: 0, TIER_PRICE_ONLY: 0}


def test_index_weight_is_optional():
    """Most of the cement sector is outside the KSE-100, so weight annotates, not defines."""
    assert _entry("THCCL", TIER_PRICE_ONLY).index_weight is None
