"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/config";

export type Freshness = { as_of: string | null; retrieved_at: string | null; sources: string[]; stale: boolean };
export type PriceSnapshot = { close: number | null; change_pct: number | null; volume: number | null; badge: string; freshness: Freshness };

export type Domain = {
  key: string;
  label: string;
  state: string;
  confidence: number | null;
  stale: boolean;
  as_of: string | null;
  inputs: { label: string; value?: number | string; previous?: number; period_end?: string }[];
  supports: string[];
  could_change: string[];
  reason: string | null;
};
export type ResearchView = {
  domains: Domain[];
  data_confidence: { level: string; passed: number; total: number; rule: string; checks: { key: string; passed: boolean; detail: string }[] };
  overall: { state: string; reason: string; assessed_domains: number; disagreements: string[] };
  methodology_version: string;
};
export type StudioEvent = {
  id: number;
  title: string;
  category: string;
  published_at: string;
  retrieved_at: string | null;
  source_url: string | null;
  source_tier: string | null;
};
export type ResearchOverview = {
  business_health: string;
  business_health_confidence: string;
  earnings_quality: string;
  earnings_quality_confidence: string;
  valuation: string;
  valuation_confidence: string;
  risk_level: string;
  what_changed: string;
  bull_thesis: string;
  bear_thesis: string;
  key_debate: string;
  red_flags: Array<{ issue?: string }>;
  watch_metrics: string[];
  data_availability: number;
};

export type Overview = {
  generated_at: string;
  security_id: number;
  symbol: string;
  name: string;
  sector: string | null;
  listing_status: string;
  what_it_does: string | null;
  profile_source: { url: string; retrieved_at: string } | null;
  price: PriceSnapshot;
  coverage: { prices: boolean; statements: boolean; profile: boolean; tier: string };
  research_overview: ResearchOverview;
  research_view?: ResearchView;
  latest_events: StudioEvent[];
};
export type SearchResult = { security_id: number; symbol: string; name: string; sector: string | null; price: PriceSnapshot };

export function studioUrl(symbol: string, endpoint: string) {
  return `${API_BASE_URL}/api/v1/companies/${encodeURIComponent(symbol)}/${endpoint}`;
}

export function useStudio<T>(symbol: string, endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);
    fetch(studioUrl(symbol, endpoint))
      .then(async (r) => {
        if (r.status === 404) throw new Error("This company is not in the covered universe.");
        if (!r.ok) throw new Error(`The API returned an error (${r.status}).`);
        return r.json();
      })
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e instanceof TypeError ? `Could not reach the research API at ${API_BASE_URL}.` : e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [symbol, endpoint]);

  return { data, error, loading };
}
