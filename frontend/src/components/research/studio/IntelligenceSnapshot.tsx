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

  const { research_view: view, price } = overview;
  const eo = view.overall;
  const conf = view.data_confidence;
  const intel = intelligence?.executive_summary;

  // Extract domain states
  const domainMap: Record<string, string | undefined> = {};
  view.domains.forEach((d) => {
    const key = d.key.toLowerCase();
    if (!key.includes("confidence")) {
      domainMap[key] = d.state;
    }
  });

  // Helper: Get domain state and build metrics
  const getDomainState = (keys: string[]): string | null => {
    for (const key of keys) {
      const s = domainMap[key];
      if (s && !["INSUFFICIENT_DATA", "UNAVAILABLE"].includes(s)) {
        return s;
      }
    }
    return null;
  };

  // Map to institutional research states
  const mapToInstitutional = (state: string | null | undefined): "positive" | "negative" | "neutral" => {
    if (!state) return "neutral";
    const s = state.toUpperCase();
    if (["IMPROVING", "POSITIVE", "FAVORABLE", "HIGH_GROWTH", "ATTRACTIVE"].includes(s)) return "positive";
    if (["DETERIORATING", "NEGATIVE", "UNFAVORABLE", "WEAK", "EXPENSIVE"].includes(s)) return "negative";
    return "neutral";
  };

  // Build metrics from domains
  const metrics: SnapshotMetric[] = [
    {
      label: "Financial Health",
      value:
        intel?.business_health && intel.business_health !== "Unknown"
          ? intel.business_health
          : getDomainState(["profitability", "leverage", "efficiency"])
            ? stateText(getDomainState(["profitability", "leverage", "efficiency"]) || "")
            : "Not assessed",
      icon: <DollarSign className="h-4 w-4" />,
      state: mapToInstitutional(intel?.business_health || getDomainState(["profitability"])),
    },
    {
      label: "Growth",
      value:
        getDomainState(["growth"])
          ? stateText(getDomainState(["growth"]) || "")
          : intelligence?.executive_summary?.business_health?.includes("Growth")
            ? "Evident"
            : "Not assessed",
      icon: <TrendingUp className="h-4 w-4" />,
      state: mapToInstitutional(getDomainState(["growth"])),
    },
    {
      label: "Valuation",
      value:
        intel?.valuation_assessment && intel.valuation_assessment !== "Unknown"
          ? intel.valuation_assessment
          : getDomainState(["valuation"])
            ? stateText(getDomainState(["valuation"]) || "")
            : "Not assessed",
      icon: <Target className="h-4 w-4" />,
      state: mapToInstitutional(intel?.valuation_assessment || getDomainState(["valuation"])),
    },
    {
      label: "Technical",
      value:
        getDomainState(["momentum", "technicals"])
          ? stateText(getDomainState(["momentum", "technicals"]) || "")
          : "Not assessed",
      icon: <Zap className="h-4 w-4" />,
      state: mapToInstitutional(getDomainState(["momentum"])),
    },
    {
      label: "Risk",
      value:
        intel?.risk_level && intel.risk_level > 0
          ? `${intel.risk_level} high-priority`
          : getDomainState(["risk", "risks"])
            ? stateText(getDomainState(["risk", "risks"]) || "")
            : "Not assessed",
      icon: <Shield className="h-4 w-4" />,
      state: mapToInstitutional(getDomainState(["risk"])) === "negative" ? "negative" : "neutral",
    },
    {
      label: "Earnings Quality",
      value:
        intel?.earnings_quality && intel.earnings_quality !== "Unknown"
          ? intel.earnings_quality
          : getDomainState(["earnings"])
            ? stateText(getDomainState(["earnings"]) || "")
            : "Not assessed",
      icon: <TrendingUp className="h-4 w-4" />,
      state: mapToInstitutional(intel?.earnings_quality),
    },
  ];

  // Extract strengths and risks (limited to 3 each)
  const strengths =
    intelligence?.intelligence?.business_health?.strengths?.slice(0, 3) ||
    view.domains
      .filter((d) => d.supports && d.supports.length > 0)
      .slice(0, 3)
      .flatMap((d) => d.supports);

  const risks =
    intelligence?.intelligence?.red_flags?.flags?.slice(0, 3).map((f) => f.issue) ||
    view.domains
      .filter((d) => d.could_change && d.could_change.length > 0)
      .slice(0, 3)
      .flatMap((d) => d.could_change);

  // Data freshness and gaps
  const allStale = view.domains.some((d) => d.stale);
  const missingDomains = view.domains.filter((d) => ["INSUFFICIENT_DATA", "UNAVAILABLE"].includes(d.state));

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
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Overall Assessment</p>
            <p className={`text-lg font-semibold ${stateTone(eo.state)}`}>{stateText(eo.state)}</p>
            <p className="mt-2 text-sm text-muted">{eo.reason}</p>
            {eo.disagreements && eo.disagreements.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs text-muted">
                {eo.disagreements.map((d) => (
                  <li key={d}>
                    <span className="text-foreground">·</span> {d}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="shrink-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Data Quality</p>
            <div className="text-right">
              <p className={`text-base font-bold ${stateTone(conf.level)}`}>{stateText(conf.level)}</p>
              <p className="text-xs text-muted mt-1">{conf.passed} of {conf.total} checks</p>
            </div>
          </div>
        </div>
      </div>

      {/* Strengths & Risks */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Key Strengths */}
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Key Strengths</p>
            {strengths && strengths.length > 0 ? (
              <ul className="space-y-1.5 text-sm">
                {strengths.slice(0, 3).map((s, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-positive" />
                    <span className="text-foreground">{s}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Missing>No verified strengths on file.</Missing>
            )}
          </div>
        </Card>

        {/* Key Risks */}
        <Card>
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Key Risks</p>
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
              <Missing>No critical risks identified.</Missing>
            )}
          </div>
        </Card>
      </div>

      {/* Data Quality Warnings */}
      {(allStale || missingDomains.length > 0) && (
        <div className="rounded-lg border border-yellow-200/50 bg-yellow-50/30 p-3.5">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
            <div className="text-xs">
              <p className="font-semibold text-yellow-900 mb-1">Data Quality Notice</p>
              <ul className="space-y-0.5 text-yellow-800">
                {allStale && <li>· Some data is stale; check source timestamps</li>}
                {missingDomains.length > 0 && (
                  <li>
                    · <span className="font-medium">{missingDomains.length}</span> assessment{missingDomains.length !== 1 ? "s" : ""} not assessable due to insufficient data
                    {missingDomains.length <= 3 && `: ${missingDomains.map((d) => d.label).join(", ")}`}
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
