"use client";
import React, { useState } from "react";
import { Search, Loader2, AlertCircle, TrendingUp, BarChart3 } from "lucide-react";
import { useRouter } from "next/navigation";

interface UnifiedResponse {
  ticker: string;
  evidence_score: {
    coverage_pct: number;
    total_sections: number;
    real_sections: number;
    overall_evidence_score: number;
  };
  gates: Array<{
    gate_name: string;
    passed: boolean;
    issue?: string;
  }>;
  thesis: {
    confidence_score: number;
    bull_case: string;
    bear_case: string;
    invalidation: string;
  };
  calculator: {
    position_size_shares: number;
    capital_required: number;
    max_loss: number;
  };
  confidence: number;
  ready_to_trade: boolean;
}

type TabType = "scorecard" | "research";

export function UnifiedResearchTradeFlow() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<UnifiedResponse | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("scorecard");

  const loadData = async (t: string) => {
    if (!t.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch("http://localhost:5000/api/research-trade/unified-flow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: t.toUpperCase(),
          entry: 250.0,
          stop: 240.0,
          targets: [260.0, 270.0, 280.0],
          portfolio_value: 100000.0,
          risk_percent: 2.0,
          trade_horizon: "MEDIUM_TERM"
        }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`API Error: ${res.status} - ${errorText || "Failed to load"}`);
      }
      const result = await res.json();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData(ticker);
  };

  const getColor = (score: number) => {
    if (score >= 75) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground">Research-to-Trade Flow</h1>
          <p className="text-muted">Module 7: Unified analysis with 6D confidence scoring</p>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Enter ticker (FFC, EFERT, etc)..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-border rounded-lg bg-surface text-foreground"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-accent text-white rounded-lg font-semibold"
          >
            Analyze
          </button>
        </form>

        {error && <div className="text-red-500">{error}</div>}
        {loading && <div className="text-center text-muted">Loading...</div>}

        {data && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface border border-border rounded-lg p-8">
                <h2 className="text-2xl font-bold">{data.ticker}</h2>
                <p className={`text-6xl font-bold mt-4 ${getColor(data.confidence)}`}>
                  {data.confidence.toFixed(0)}/100
                </p>
                <p className="text-xs text-muted mt-2">Confidence Score</p>
              </div>

              <div className="bg-surface border border-border rounded-lg p-8">
                <h3 className="font-semibold">Evidence Coverage</h3>
                <p className={`text-3xl font-bold mt-4`}>
                  {data.evidence_score.coverage_pct.toFixed(0)}%
                </p>
                <p className="text-xs text-muted mt-2">{data.evidence_score.real_sections}/{data.evidence_score.total_sections} sections</p>
              </div>
            </div>

            <div className={`border-2 rounded-lg p-6 ${
              data.ready_to_trade ? "bg-green-500/20 border-green-500 text-green-500" : "bg-yellow-500/20 border-yellow-500 text-yellow-500"
            }`}>
              <p className="text-3xl font-bold">{data.ready_to_trade ? "READY TO TRADE" : "CAUTION - REVIEW GATES"}</p>
              <p className="text-sm mt-2">
                {data.gates.filter(g => !g.passed).map(g => g.issue).filter(Boolean).join("; ") || "All gates passed"}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Bull Case</h3>
                <p className="text-sm text-muted">{data.thesis.bull_case}</p>
              </div>

              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Bear Case</h3>
                <p className="text-sm text-muted">{data.thesis.bear_case}</p>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-lg p-6">
              <h3 className="font-semibold mb-3">Position Sizing</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-muted">Shares</p>
                  <p className="text-2xl font-bold">{data.calculator.position_size_shares}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Capital</p>
                  <p className="text-2xl font-bold">PKR {(data.calculator.capital_required / 1000).toFixed(0)}k</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Max Loss</p>
                  <p className="text-2xl font-bold">PKR {data.calculator.max_loss.toFixed(0)}</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => router.push(`/trade-planning?ticker=${data.ticker}`)}
              className="w-full px-6 py-3 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90"
            >
              Proceed to Trade Planning →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
