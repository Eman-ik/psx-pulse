"use client";
import React, { useState } from "react";
import { Search, Loader2, AlertCircle, TrendingUp, BarChart3, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { formatRupees, formatPercent, formatRatio } from "@/lib/format";

interface ResearchData {
  company: {
    ticker: string;
    legal_name: string;
    sector: string;
    market_cap: number;
    stock_price: number;
    shares_outstanding: number;
    free_float: number;
  };
  financials: {
    revenue: number;
    pat: number;
    eps: number;
  };
  metrics: {
    eps: number;
    roe: number;
    pe_ratio: number;
    net_margin: number;
    debt_to_equity: number;
    dividend_yield: number;
  };
  valuation: {
    pe_ratio: number;
    dividend_yield: number;
    market_cap: number;
    stock_price: number;
  };
}

type TabType = "overview" | "financials" | "metrics" | "valuation";

export function ResearchStudio() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ResearchData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  const loadData = async (t: string) => {
    if (!t.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    setActiveTab("overview");

    try {
      const res = await fetch(`http://localhost:5000/api/research/${t.toUpperCase()}/data`);
      if (!res.ok) throw new Error("Company not found");
      const result = await res.json();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error loading data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData(ticker);
  };

  const TABS = [
    { id: "overview" as TabType, label: "Overview" },
    { id: "financials" as TabType, label: "Financials" },
    { id: "metrics" as TabType, label: "Metrics" },
    { id: "valuation" as TabType, label: "Valuation" },
  ];

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground">Research Studio</h1>
          <p className="text-muted">Complete financial data for PSX companies</p>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Enter ticker (FFC, EFERT, FATIMA...)"
              disabled={loading}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-surface text-foreground focus:outline-none focus:ring-1 focus:ring-accent disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className="px-6 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg disabled:opacity-50 font-semibold flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
          </button>
        </form>

        <div className="flex gap-2 flex-wrap justify-center">
          {["FFC", "EFERT", "FATIMA", "IFIC", "LUCK", "DGKC", "CHCC", "PCCL"].map((t) => (
            <button
              key={t}
              onClick={() => { setTicker(t); loadData(t); }}
              disabled={loading}
              className="px-3 py-1 text-sm border border-border rounded hover:border-accent text-muted hover:text-foreground disabled:opacity-50"
            >
              {t}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-negative/10 border border-negative/30 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-negative shrink-0" />
            <div>
              <p className="font-semibold text-negative">Error</p>
              <p className="text-sm text-muted">{error}</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-accent" />
            <p className="text-muted mt-2">Loading data...</p>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-6">
            <div className="bg-surface border border-border rounded-lg p-6">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-foreground">{data.company.legal_name}</h2>
                  <p className="text-sm text-muted mt-1">Ticker: {data.company.ticker} • {data.company.sector}</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-foreground">{formatRupees(data.company.stock_price)}</p>
                  <p className="text-xs text-muted">Current Price</p>
                </div>
              </div>
            </div>

            <div className="border-b border-border flex gap-1 overflow-x-auto">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id ? "border-accent text-accent" : "border-transparent text-muted hover:text-foreground"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === "overview" && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Stock Price", value: formatRupees(data.company.stock_price) },
                  { label: "Market Cap", value: formatRupees(data.company.market_cap, "billions") },
                  { label: "Shares Outstanding", value: formatRupees(data.company.shares_outstanding, "millions") },
                  { label: "Free Float", value: formatPercent(data.company.free_float) },
                ].map((m) => (
                  <div key={m.label} className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-xs text-muted uppercase mb-2">{m.label}</p>
                    <p className="text-lg font-bold text-foreground">{m.value}</p>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "financials" && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { label: "Revenue", value: formatRupees(data.financials.revenue, "billions"), sub: "Annual Revenue" },
                  { label: "PAT", value: formatRupees(data.financials.pat, "billions"), sub: "Profit After Tax" },
                  { label: "EPS", value: formatRupees(data.financials.eps), sub: "Earnings Per Share" },
                ].map((m) => (
                  <div key={m.label} className="bg-surface border border-border rounded-lg p-6">
                    <p className="text-xs text-muted uppercase mb-2">{m.label}</p>
                    <p className="text-2xl font-bold text-foreground">{m.value}</p>
                    <p className="text-xs text-muted mt-2">{m.sub}</p>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "metrics" && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  { label: "ROE", value: formatPercent(data.metrics.roe), desc: "Return on Equity" },
                  { label: "Net Margin", value: formatPercent(data.metrics.net_margin), desc: "Net Profit Margin" },
                  { label: "D/E Ratio", value: formatRatio(data.metrics.debt_to_equity), desc: "Debt to Equity" },
                  { label: "P/E Ratio", value: formatRatio(data.metrics.pe_ratio), desc: "Price to Earnings" },
                  { label: "Div Yield", value: formatPercent(data.metrics.dividend_yield), desc: "Dividend Yield" },
                  { label: "EPS", value: formatRupees(data.metrics.eps), desc: "Earnings Per Share" },
                ].map((m) => (
                  <div key={m.label} className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-xs text-muted uppercase mb-1">{m.label}</p>
                    <p className="text-xl font-bold text-foreground">{m.value}</p>
                    <p className="text-[11px] text-muted/70 mt-1">{m.desc}</p>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "valuation" && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="font-semibold text-foreground mb-4">Valuation Metrics</h3>
                <div className="space-y-3">
                  {[
                    { label: "P/E Ratio", value: formatRatio(data.valuation.pe_ratio) },
                    { label: "Dividend Yield", value: formatPercent(data.valuation.dividend_yield) },
                    { label: "Market Cap", value: formatRupees(data.valuation.market_cap, "billions") },
                    { label: "Stock Price", value: formatRupees(data.valuation.stock_price) },
                  ].map((m) => (
                    <div key={m.label} className="flex items-center justify-between pb-3 border-b border-border/30 last:border-0">
                      <span className="text-muted">{m.label}</span>
                      <span className="font-bold text-foreground">{m.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-accent/10 border border-accent/30 rounded-lg p-6 flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="font-semibold text-foreground">Ready to trade?</p>
                <p className="text-sm text-muted">Use our position sizing calculator</p>
              </div>
              <button
                onClick={() => router.push(`/trade-planning?ticker=${data.company.ticker}`)}
                className="px-6 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg font-semibold flex items-center gap-2 whitespace-nowrap"
              >
                <TrendingUp className="w-4 h-4" /> Plan Trade
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
