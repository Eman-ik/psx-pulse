"use client";
import React, { useState } from "react";
import { Search, Loader2, AlertCircle, TrendingUp, BarChart3 } from "lucide-react";
import { useRouter } from "next/navigation";

interface UnifiedResponse {
  success: boolean;
  ticker: string;
  company: any;
  unified_confidence_score: number;
  entry_recommendation: string;
  key_reasons: string[];
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
        body: JSON.stringify({ ticker: t.toUpperCase() }),
      });

      if (!res.ok) throw new Error("Failed to load");
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
            <div className="bg-surface border border-border rounded-lg p-8">
              <h2 className="text-3xl font-bold">{data.company.legal_name}</h2>
              <p className={`text-6xl font-bold mt-4 ${getColor(data.unified_confidence_score)}`}>
                {data.unified_confidence_score.toFixed(0)}/100
              </p>
            </div>

            <div className={`border-2 rounded-lg p-6 ${
              data.entry_recommendation === "ENTER" ? "bg-green-500/20 border-green-500 text-green-500" :
              data.entry_recommendation === "CAUTION" ? "bg-yellow-500/20 border-yellow-500 text-yellow-500" :
              data.entry_recommendation === "WAIT" ? "bg-blue-500/20 border-blue-500 text-blue-500" :
              "bg-red-500/20 border-red-500 text-red-500"
            }`}>
              <p className="text-3xl font-bold">{data.entry_recommendation}</p>
            </div>

            <div className="bg-surface border border-border rounded-lg p-6">
              <h3 className="font-semibold mb-3">Key Reasons</h3>
              {data.key_reasons.map((r, i) => <div key={i} className="text-sm text-muted">✓ {r}</div>)}
            </div>

            <button
              onClick={() => router.push(`/trade-planning?ticker=${data.ticker}`)}
              className="w-full px-6 py-3 bg-accent text-white rounded-lg font-semibold"
            >
              Proceed to Trade Planning →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
