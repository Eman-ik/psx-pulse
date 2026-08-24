"use client";

import { useEffect, useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Trash2, Plus, AlertTriangle } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatPct, formatPrice } from "@/lib/format";
import { DONUT_COLORS } from "@/components/dashboard/MarketCapDonut";
import { mergeLiveQuote, useLiveQuotes } from "@/lib/useLiveQuotes";

const STORAGE_KEY = "psx_portfolio";

/** Individual holdings are PKR thousands-to-low-millions, not company-scale billions --
 * formatMarketCap (which divides by 1e6 for a "bn" suffix) would render a real holding as a
 * meaningless "PKR 0.1 bn". This formats a plain PKR amount with thousands separators instead.
 */
function formatCurrency(v: number): string {
  return `PKR ${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

interface Holding {
  companyId: number;
  quantity: number;
  avgCost: number;
}

const SIGNAL_COLORS: Record<string, string> = {
  strong_buy: "#22c55e",
  buy: "#4ade80",
  hold: "#f59e0b",
  sell: "#fb923c",
  strong_sell: "#ef4444",
  no_signal: "#6b7280",
};

function loadHoldings(): Holding[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Holding[]) : [];
  } catch {
    return [];
  }
}

function saveHoldings(holdings: Holding[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">{label}</p>
      <p className="text-xl font-bold tabular-nums" style={color ? { color } : undefined}>{value}</p>
    </div>
  );
}

export default function PortfolioView({ rows: rawRows }: { rows: ComparisonRow[] }) {
  // rawRows arrive price-null from SSR (fast, DB-only -- see comparison.py); market value
  // and P&L below need a real price, so live quotes are merged in before anything else.
  const { quotesBySymbol } = useLiveQuotes();
  const rows = useMemo(
    () => rawRows.map((r) => (r.symbol ? mergeLiveQuote(r, quotesBySymbol[r.symbol]) : r)),
    [rawRows, quotesBySymbol]
  );

  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [quantity, setQuantity] = useState("");
  const [avgCost, setAvgCost] = useState("");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // Reading localStorage during the initial client render (instead of here, post-mount)
    // would mismatch the server-rendered HTML, which always has no access to localStorage --
    // same pattern already used by AISignalTab.tsx's watchlist effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHoldings(loadHoldings());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveHoldings(holdings);
  }, [holdings, hydrated]);

  const byId = useMemo(() => new Map(rows.map((r) => [r.id, r])), [rows]);
  const heldIds = new Set(holdings.map((h) => h.companyId));
  const availableRows = rows.filter((r) => !heldIds.has(r.id) && r.price != null);

  function addHolding() {
    const qty = Number(quantity);
    const cost = Number(avgCost);
    if (selectedId === "" || !Number.isFinite(qty) || qty <= 0 || !Number.isFinite(cost) || cost <= 0) return;
    setHoldings((prev) => [...prev, { companyId: Number(selectedId), quantity: qty, avgCost: cost }]);
    setSelectedId("");
    setQuantity("");
    setAvgCost("");
  }

  function removeHolding(companyId: number) {
    setHoldings((prev) => prev.filter((h) => h.companyId !== companyId));
  }

  const enriched = holdings
    .map((h) => {
      const row = byId.get(h.companyId);
      if (!row || row.price == null) return null;
      const marketValue = row.price * h.quantity;
      const costBasis = h.avgCost * h.quantity;
      const pnl = marketValue - costBasis;
      const pnlPct = costBasis > 0 ? (pnl / costBasis) * 100 : null;
      return { holding: h, row, marketValue, costBasis, pnl, pnlPct };
    })
    .filter((x): x is NonNullable<typeof x> => x !== null);

  const totalMarketValue = enriched.reduce((s, x) => s + x.marketValue, 0);
  const totalCostBasis = enriched.reduce((s, x) => s + x.costBasis, 0);
  const totalPnl = totalMarketValue - totalCostBasis;
  const totalPnlPct = totalCostBasis > 0 ? (totalPnl / totalCostBasis) * 100 : null;

  const compositionData = enriched.map((x) => ({ name: x.row.symbol ?? x.row.name, value: x.marketValue }));

  const signalCounts = enriched.reduce<Record<string, number>>((acc, x) => {
    const key = x.row.ai_signal ?? "no_signal";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  const signalData = Object.entries(signalCounts).map(([name, value]) => ({ name, value }));

  if (!hydrated) return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Add holding form */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <h2 className="mb-4 text-sm font-semibold">Add a holding</h2>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted">Company</span>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : "")}
              className="rounded-lg border border-border bg-surface-alt px-3 py-2 text-sm text-foreground"
            >
              <option value="">Select a company…</option>
              {availableRows.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.symbol ?? r.name} — {r.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted">Quantity</span>
            <input
              type="number"
              min="0"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-28 rounded-lg border border-border bg-surface-alt px-3 py-2 text-sm text-foreground"
              placeholder="0"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-muted">Avg cost (PKR)</span>
            <input
              type="number"
              min="0"
              step="0.01"
              value={avgCost}
              onChange={(e) => setAvgCost(e.target.value)}
              className="w-32 rounded-lg border border-border bg-surface-alt px-3 py-2 text-sm text-foreground"
              placeholder="0.00"
            />
          </label>
          <button
            onClick={addHolding}
            disabled={selectedId === "" || !quantity || !avgCost}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Plus size={15} /> Add
          </button>
        </div>
      </div>

      {enriched.length === 0 ? (
        <p className="text-sm text-muted">No holdings yet — add one above to start tracking.</p>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Market Value" value={formatCurrency(totalMarketValue)} />
            <StatCard label="Cost Basis" value={formatCurrency(totalCostBasis)} />
            <StatCard
              label="Total P&L"
              value={formatCurrency(totalPnl)}
              color={totalPnl >= 0 ? "#22c55e" : "#ef4444"}
            />
            <StatCard
              label="Total P&L %"
              value={totalPnlPct != null ? formatPct(totalPnlPct) : "—"}
              color={totalPnlPct != null && totalPnlPct >= 0 ? "#22c55e" : "#ef4444"}
            />
          </div>

          {/* Donuts */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold">Composition by market value</h3>
              <div className="relative h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={compositionData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={75} paddingAngle={3} strokeWidth={0}>
                      {compositionData.map((entry, i) => (
                        <Cell key={entry.name} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                      formatter={(value: number, name) => [formatCurrency(value), name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold">AI signal exposure</h3>
              <div className="relative h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={signalData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={75} paddingAngle={3} strokeWidth={0}>
                      {signalData.map((entry) => (
                        <Cell key={entry.name} fill={SIGNAL_COLORS[entry.name] ?? "#6b7280"} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                      formatter={(value: number, name) => [`${value} holding${value === 1 ? "" : "s"}`, name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Holdings table */}
          <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted">
                  <th className="px-4 py-3 font-normal">Company</th>
                  <th className="px-4 py-3 text-right font-normal">Qty</th>
                  <th className="px-4 py-3 text-right font-normal">Avg Cost</th>
                  <th className="px-4 py-3 text-right font-normal">Price</th>
                  <th className="px-4 py-3 text-right font-normal">Market Value</th>
                  <th className="px-4 py-3 text-right font-normal">P&L</th>
                  <th className="px-4 py-3 text-right font-normal">P&L %</th>
                  <th className="px-4 py-3 text-left font-normal">AI Signal</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {enriched.map(({ holding, row, marketValue, pnl, pnlPct }) => (
                  <tr key={holding.companyId} className="border-b border-border/40 last:border-0">
                    <td className="px-4 py-3">
                      <p className="font-medium">{row.symbol ?? row.name}</p>
                      <p className="text-xs text-muted">{row.name}</p>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{holding.quantity}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPrice(holding.avgCost)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatPrice(row.price)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(marketValue)}</td>
                    <td className={`px-4 py-3 text-right tabular-nums ${pnl >= 0 ? "text-positive" : "text-negative"}`}>
                      {formatCurrency(pnl)}
                    </td>
                    <td className={`px-4 py-3 text-right tabular-nums ${pnlPct != null && pnlPct >= 0 ? "text-positive" : "text-negative"}`}>
                      {pnlPct != null ? formatPct(pnlPct) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="rounded-full px-2 py-0.5 text-[11px] font-medium capitalize"
                        style={{
                          color: SIGNAL_COLORS[row.ai_signal ?? "no_signal"],
                          backgroundColor: `${SIGNAL_COLORS[row.ai_signal ?? "no_signal"]}18`,
                        }}
                      >
                        {(row.ai_signal ?? "no_signal").replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => removeHolding(holding.companyId)} className="text-muted hover:text-negative">
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="flex items-start gap-3 rounded-2xl border border-accent-yellow/30 bg-accent-yellow/5 p-4 text-xs text-muted">
        <AlertTriangle size={16} className="mt-0.5 shrink-0 text-accent-yellow" />
        <p>
          This is a personal tracking tool, not a brokerage account. Holdings are stored only in
          your browser&apos;s local storage and are never transmitted anywhere. Prices are the
          platform&apos;s latest on-file quotes, which may be delayed — see each company page for
          the exact data-delay disclosure.
        </p>
      </div>
    </div>
  );
}
