"""Tests for fetch_live_snapshot's timeout/retry/circuit-breaker wrapper -- added
after finding psxdata batches returning 0/16 within their own 35s cap under
concurrent load, and after the single-fetch path (no timeout at all before this)
was found capable of hanging a request indefinitely.

Monkeypatches app.ingestion.psx_live._fetch_live_snapshot_once directly rather than
psxdata itself, since the wrapper's own retry/circuit-breaker logic is what's under
test here, not psxdata's real behavior (already covered by manual verification --
see the async-live-quotes and price-discontinuity work this session).
"""

import time

import pytest

from app.ingestion import psx_live


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """Every test starts with a closed circuit and a clean failure count -- these are
    module-level globals, so tests would otherwise leak state into each other."""
    psx_live._circuit_consecutive_failures = 0
    psx_live._circuit_open_until = 0.0
    yield
    psx_live._circuit_consecutive_failures = 0
    psx_live._circuit_open_until = 0.0


def test_successful_fetch_resets_failure_count(monkeypatch):
    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", lambda symbol, use_cache: {"symbol": symbol, "price": 100.0})
    psx_live._circuit_consecutive_failures = 3

    result = psx_live.fetch_live_snapshot("FFC", retry=False)

    assert result == {"symbol": "FFC", "price": 100.0}
    assert psx_live._circuit_consecutive_failures == 0


def test_retry_true_makes_a_second_attempt_after_a_failure(monkeypatch):
    calls = []

    def flaky(symbol, use_cache):
        calls.append(symbol)
        if len(calls) == 1:
            return None
        return {"symbol": symbol, "price": 100.0}

    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", flaky)
    monkeypatch.setattr(psx_live.time, "sleep", lambda _: None)  # skip the real backoff

    result = psx_live.fetch_live_snapshot("FFC", retry=True)

    assert len(calls) == 2
    assert result == {"symbol": "FFC", "price": 100.0}


def test_retry_false_gives_up_after_one_failed_attempt(monkeypatch):
    calls = []
    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", lambda symbol, use_cache: calls.append(symbol) or None)

    result = psx_live.fetch_live_snapshot("FFC", retry=False)

    assert len(calls) == 1
    assert result is None


def test_circuit_opens_after_threshold_consecutive_failures(monkeypatch):
    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", lambda symbol, use_cache: None)
    monkeypatch.setattr(psx_live.time, "sleep", lambda _: None)

    for _ in range(psx_live._CIRCUIT_FAILURE_THRESHOLD):
        psx_live.fetch_live_snapshot("FFC", retry=False)

    assert psx_live._circuit_consecutive_failures == psx_live._CIRCUIT_FAILURE_THRESHOLD
    assert psx_live._circuit_open_until > time.monotonic()


def test_open_circuit_short_circuits_without_calling_the_source(monkeypatch):
    calls = []
    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", lambda symbol, use_cache: calls.append(symbol) or None)
    psx_live._circuit_open_until = time.monotonic() + 60

    result = psx_live.fetch_live_snapshot("FFC", retry=False)

    assert result is None
    assert calls == []  # the real fetch function was never even attempted


def test_expired_circuit_allows_a_real_attempt_again(monkeypatch):
    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", lambda symbol, use_cache: {"symbol": symbol, "price": 100.0})
    psx_live._circuit_open_until = time.monotonic() - 1  # already expired

    result = psx_live.fetch_live_snapshot("FFC", retry=False)

    assert result == {"symbol": "FFC", "price": 100.0}


def test_fetch_that_raises_is_treated_as_a_failure_not_propagated(monkeypatch):
    def boom(symbol, use_cache):
        raise RuntimeError("simulated psxdata crash")

    monkeypatch.setattr(psx_live, "_fetch_live_snapshot_once", boom)

    result = psx_live.fetch_live_snapshot("FFC", retry=False)

    assert result is None
    assert psx_live._circuit_consecutive_failures == 1
