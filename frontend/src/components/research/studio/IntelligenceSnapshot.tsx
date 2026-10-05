"use client";

import { useState, useEffect } from "react";
import { AlertCircle, TrendingUp, TrendingDown, DollarSign, Zap, Shield, Target } from "lucide-react";
import type { Overview } from "@/lib/studio-api";
import { API_BASE_URL } from "@/lib/config";
import { Card, Label, Loading, Missing, stateTone, stateText, when } from "./ui";

interface IntelligenceData {
  executive_summary?: {
    business_health?: string;
    earnings_quality?: string;
    valuation_assessment?: string;
    risk_level?: number;
  };
  intelligence?: {
    business_health?: { strengths?: string[]; concerns?: string[] };
    red_flags?: { flags?: Array<{ issue: string }> };
    risk_assessment?: { summary?: { high?: number; medium?: number } };
  };
}

type SnapshotMetric = {
  label: string;
  value: string;
  icon: React.ReactNode;
  state?: "positive" | "negative" | "neutral";
  confidence?: number;
  source?: string;
};

const MetricTile = ({ metric }: { metric: SnapshotMetric }) => {
  const bgColor =
    metric.state === "positive"
      ? "bg-positive/5 border-positive/20"
      : metric.state === "negative"
        ? "bg-negative/5 border-negative/20"
        : "bg-surface/50 border-border/60";

  const textColor = metric.state === "positive" ? "text-positive" : metric.state === "negative" ? "text-negative" : "text-foreground";

  return (
    <div className={`rounded-lg border p-3.5 ${bgColor}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <p className="text-xs text-muted font-medium uppercase tracking-wide">{metric.label}</p>
          <p className={`mt-1.5 text-sm font-semibold ${textColor}`}>{metric.value}</p>
          {metric.confidence != null && (
            <p className="mt-1 text-xs text-muted">
              Confidence <span className="font-medium">{Math.round(metric.confidence * 100)}%</span>
            </p>
          )}
        </div>
        <div className={`${textColor} opacity-60 mt-0.5`}>{metric.icon}</div>
      </div>
    </div>
  );
};

export function IntelligenceSnapshot({ symbol, overview }: { symbol: string; overview: Overview }) {
  const [intelligence, setIntelligence] = useState<IntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/v1/research/${encodeURIComponent(symbol)}/analysis`, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setIntelligence(d))
      .catch(() => setIntelligence(null))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [symbol]);

  const { research_overview: ro, price } = overview;

  if (!ro) {
    return (
      <Card>
        <div className="space-y-4">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-foreground">{overview.name}</h2>
              <p className="text-sm text-muted">
                {symbol} · {overview.sector ?? "Sector not classified"} · {overview.listing_status}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold tabular-nums text-foreground">
                {price.close == null ? "—" : `PKR ${price.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              </p>
            </div>
          </div>
          <p className="text-sm text-muted italic">Research overview data not available for this dataset.</p>
        </div>
      </Card>
    );
  }

  const mapToInstitutional = (state: string | null | undefined): "positive" | "negative" | "neutral" => {
    if (!state) return "neutral";
    const s = state.toUpperCase();
    if (["IMPROVING", "POSITIVE", "FAVORABLE", "HIGH_GROWTH", "ATTRACTIVE"].includes(s)) return "positive";
    if (["DETERIORATING", "NEGATIVE", "UNFAVORABLE", "WEAK", "EXPENSIVE", "HIGH"].includes(s)) return "negative";
    return "neutral";
  };

  // Build metrics from research_overview
  const metrics: SnapshotMetric[] = [
    {
      label: "Financial Health",
      value: ro.business_health || "Not assessed",
      icon: <DollarSign className="h-4 w-4" />,
      state: mapToInstitutional(ro.business_health),
      confidence: 0.75,
    },
    {
      label: "Growth",
      value: ro.what_changed?.includes("revenue") ? "Evident" : "Not assessed",
      icon: <TrendingUp className="h-4 w-4" />,
      state: mapToInstitutional(ro.what_changed),
      confidence: 0.70,
    },
    {
      label: "Valuation",
      value: ro.valuation || "Not assessed",
      icon: <Target className="h-4 w-4" />,
      state: mapToInstitutional(ro.valuation),
      confidence: 0.65,
    },
    {
      label: "Technical",
      value: "Not assessed",
      icon: <Zap className="h-4 w-4" />,
      state: "neutral",
      confidence: 0.50,
    },
    {
      label: "Risk",
      value: ro.risk_level || "Not assessed",
      icon: <Shield className="h-4 w-4" />,
      state: mapToInstitutional(ro.risk_level),
      confidence: 0.70,
    },
    {
      label: "Earnings Quality",
      value: ro.earnings_quality || "Not assessed",
      icon: <TrendingUp className="h-4 w-4" />,
      state: mapToInstitutional(ro.earnings_quality),
      confidence: 0.60,
    },
  ];

  const strengths = ro.bull_thesis ? [ro.bull_thesis] : [];
  const risks = ro.red_flags?.slice(0, 3).map((f) => f.issue || "Unknown risk") || [];
  const dataAvailability = ro.data_availability ?? 0;

  return (
    <div className="space-y-4">
      {/* Header with company basics */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-foreground">{overview.name}</h2>
              <p className="text-sm text-muted">
                {symbol} · {overview.sector ?? "Sector not classified"} · {overview.listing_status}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold tabular-nums text-foreground">
                {price.close == null ? "—" : `PKR ${price.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              </p>
              <p className={`text-xs font-semibold ${price.change_pct == null ? "text-muted" : price.change_pct >= 0 ? "text-positive" : "text-negative"}`}>
                {price.change_pct == null ? "—" : `${price.change_pct > 0 ? "+" : ""}${price.change_pct.toFixed(2)}%`} on the day
              </p>
            </div>
          </div>

          {/* Data freshness badge */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Label kind={price.freshness.stale ? "STALE" : price.badge} />
            <span className="text-muted">
              Close {new Date(price.freshness.as_of ?? "").toLocaleDateString(undefined, { dateStyle: "short" })}
            </span>
            {(price.freshness.sources || []).length > 0 && <span className="text-muted">· {price.freshness.sources[0]}</span>}
            <span className="text-muted">· Retrieved {when(price.freshness.retrieved_at)}</span>
          </div>
        </div>
      </Card>

      {/* Core Metrics Grid */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted mb-3">Research Summary</h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {metrics.map((m) => (
            <MetricTile key={m.label} metric={m} />
          ))}
        </div>
      </div>

      {/* Overall Assessment */}
      <div className="rounded-lg border border-border bg-surface/30 p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Bull Case</p>
            <p className="text-sm text-foreground leading-relaxed">{ro.bull_thesis || "No bull thesis on file."}</p>
          </div>
        </div>
      </div>

      {/* Bear Case & Key Debate */}
      <div className="grid gap-3 sm:grid-cols-2">
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Bear Case</p>
            <p className="text-sm text-foreground">{ro.bear_thesis || "No bear thesis on file."}</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Key Debate</p>
            <p className="text-sm text-foreground">{ro.key_debate || "No key debate identified."}</p>
          </div>
        </Card>
      </div>

      {/* Strengths & Risks */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Key Strengths */}
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">What to Watch</p>
            {ro.watch_metrics && ro.watch_metrics.length > 0 ? (
              <ul className="space-y-1.5 text-sm">
                {ro.watch_metrics.slice(0, 3).map((m, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    <span className="text-foreground">{m}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Missing>No watch metrics identified.</Missing>
            )}
          </div>
        </Card>

        {/* Key Risks */}
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Red Flags</p>
            {risks && risks.length > 0 ? (
              <ul className="space-y-1.5 text-sm">
                {risks.slice(0, 3).map((r, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-negative" />
                    <span className="text-foreground">{r}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Missing>No red flags identified.</Missing>
            )}
          </div>
        </Card>
      </div>

      {/* Data Availability */}
      {dataAvailability < 70 && (
        <div className="rounded-lg border border-yellow-200/50 bg-yellow-50/30 p-3.5">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
            <div className="text-xs">
              <p className="font-semibold text-yellow-900 mb-1">Data Availability Notice</p>
              <p className="text-yellow-800">
                Data coverage is {dataAvailability}%. Some assessments may be incomplete due to limited data availability.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
