"use client";

import { useEffect, useState } from "react";
import type { ComparisonRow, LiveQuote } from "@/lib/api";
import { fetchLiveQuotesAll, fetchSingleLiveQuote } from "@/lib/api";

// The batch scrape behind fetchLiveQuotesAll() is an unofficial, no-SLA site scrape
// (see app/ingestion/psx_live.py) that empirically sometimes comes back with zero
// quotes on a transient failure and succeeds again moments later -- confirmed directly
// (2026-08-27): one call returned quotes: [], a retry ~30s later returned real data for
// every symbol. Without a retry, that one bad scrape left every "live" price/chg%/P-E/
// div-yield cell blank for the rest of the page's session. Short backoff, then a longer
// one, before accepting "no live data" as the real answer.
const RETRY_DELAYS_MS = [5000, 15000];
// Keeps a page left open self-healing rather than frozen on whatever the scrape
// returned at mount -- same "live" framing this data already claims elsewhere.
const REFRESH_INTERVAL_MS = 90_000;

/**
 * Fetches the combined fertilizer+cement live-quote batch client-side, after the page
 * that calls this has already rendered with fast DB-only data (see comparison.py's
 * docstring for why this moved off the SSR critical path). `loading` starts true and
 * flips to false once the scrape resolves (up to ~35s, plus retries) or exhausts its
 * retries -- callers should treat `loading` as "prices not in yet", not as a blocking
 * state.
 */
export function useLiveQuotes(options?: { skip?: boolean }): {
  quotesBySymbol: Record<string, LiveQuote>;
  isLive: boolean;
  loading: boolean;
} {
  const skip = options?.skip ?? false;
  const [quotesBySymbol, setQuotesBySymbol] = useState<Record<string, LiveQuote>>({});
  const [loading, setLoading] = useState(!skip);

  useEffect(() => {
    if (skip) return;
    let cancelled = false;
    const timers: ReturnType<typeof setTimeout>[] = [];

    const load = (attempt: number) => {
      fetchLiveQuotesAll().then((res) => {
        if (cancelled) return;
        const quotes = res?.quotes ?? [];
        if (quotes.length === 0 && attempt < RETRY_DELAYS_MS.length) {
          timers.push(setTimeout(() => load(attempt + 1), RETRY_DELAYS_MS[attempt]));
          return;
        }
        // Merge rather than replace: the batch itself is best-effort per-symbol (see
        // _LIVE_QUOTE_BATCH_TIMEOUT_S's comment in psx_live.py -- a symbol that hasn't
        // responded by the batch deadline is just dropped from that response, not
        // retried server-side). A single fetch is very often partial, so each poll
        // should only ever fill in gaps, never erase a symbol that a previous poll
        // already got real data for.
        if (quotes.length > 0) {
          setQuotesBySymbol((prev) => {
            const next = { ...prev };
            for (const q of quotes) next[q.symbol] = q;
            return next;
          });
        }
        setLoading(false);
      });
    };

    load(0);
    const refresh = setInterval(() => load(0), REFRESH_INTERVAL_MS);

    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
      clearInterval(refresh);
    };
  }, [skip]);

  return { quotesBySymbol, isLive: Object.keys(quotesBySymbol).length > 0, loading };
}

/** Single-symbol counterpart for a company page's own header/price display. */
export function useLiveQuote(symbol: string | null): { quote: LiveQuote | null; loading: boolean } {
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [loading, setLoading] = useState(symbol != null);

  useEffect(() => {
    // No setState here for the null-symbol case -- that's derived at render time
    // below instead (react-hooks/set-state-in-effect: calling setState synchronously
    // in an effect body causes an extra render; a null symbol needing a null/false
    // result is a pure function of the prop, not something to sync via an effect).
    if (!symbol) return;
    let cancelled = false;
    // Needs to be synchronous: this signals "a new fetch just started" so the UI
    // shows a loading state immediately instead of the previous symbol's stale data
    // while the new fetch is in flight -- one of the most standard data-fetching
    // patterns in React, not the "derive instead of sync" case this rule targets.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    fetchSingleLiveQuote(symbol).then((res) => {
      if (cancelled) return;
      setQuote(res?.quote ?? null);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return symbol ? { quote, loading } : { quote: null, loading: false };
}

/**
 * Overlays a live quote onto a DB-only ComparisonRow, reproducing the same P/E and
 * dividend-yield fallback GET /companies/comparison used to compute server-side (see
 * that endpoint's docstring) -- psxdata's own pe_ratio/dividend_yield win when present,
 * otherwise it's derived from the live price against the row's on-file EPS/DPS.
 */
export function mergeLiveQuote(row: ComparisonRow, quote: LiveQuote | undefined): ComparisonRow {
  if (!quote) return row;
  const price = quote.price;

  let peRatio = quote.pe_ratio;
  if (peRatio == null && price && row.eps && row.eps > 0) {
    peRatio = Math.round((price / row.eps) * 100) / 100;
  }

  let dividendYield = quote.dividend_yield;
  if (dividendYield == null && price && row.dividend_per_share && price > 0) {
    dividendYield = Math.round((row.dividend_per_share / price) * 100 * 100) / 100;
  }

  return {
    ...row,
    price: price ?? row.price,
    change_pct: quote.change_pct ?? row.change_pct,
    pe_ratio: peRatio ?? row.pe_ratio,
    dividend_yield: dividendYield ?? row.dividend_yield,
  };
}
