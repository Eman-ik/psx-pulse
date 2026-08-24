"use client";

import { useEffect, useState } from "react";
import type { ComparisonRow, LiveQuote } from "@/lib/api";
import { fetchLiveQuotesAll, fetchSingleLiveQuote } from "@/lib/api";

/**
 * Fetches the combined fertilizer+cement live-quote batch client-side, after the page
 * that calls this has already rendered with fast DB-only data (see comparison.py's
 * docstring for why this moved off the SSR critical path). `loading` starts true and
 * flips to false once the scrape resolves (up to ~35s) or fails -- callers should treat
 * `loading` as "prices not in yet", not as a blocking state.
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
    fetchLiveQuotesAll().then((res) => {
      if (cancelled) return;
      const map: Record<string, LiveQuote> = {};
      for (const q of res?.quotes ?? []) map[q.symbol] = q;
      setQuotesBySymbol(map);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [skip]);

  return { quotesBySymbol, isLive: Object.keys(quotesBySymbol).length > 0, loading };
}

/** Single-symbol counterpart for a company page's own header/price display. */
export function useLiveQuote(symbol: string | null): { quote: LiveQuote | null; loading: boolean } {
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [loading, setLoading] = useState(symbol != null);

  useEffect(() => {
    if (!symbol) {
      setQuote(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
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

  return { quote, loading };
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
