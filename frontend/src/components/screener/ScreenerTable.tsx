"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDown, ArrowUp, ArrowUpDown, Info, RotateCcw, Search, Microscope } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatLiveRatio, formatMarketCap, formatMultiple, formatPct, formatPercent, formatPrice } from "@/lib/format";
import { mergeLiveQuote, useLiveQuotes } from "@/lib/useLiveQuotes";
import CoverageBadge from "@/components/shared/CoverageBadge";

type SortKey =
  | "price" | "change_pct" | "market_cap" | "pe_ratio" | "roe" | "roa" | "dividend_yield"
  | "debt_to_equity" | "current_ratio" | "net_profit_margin" | "revenue_growth_yoy"
  | "eps_growth_yoy" | "ai_score";
type SortDirection = "asc" | "desc";

interface Column {
  key: SortKey;
  label: string;
  format: (v: number | null) => string;
  // Market cap is stored in PKR thousands; filter inputs are in PKR bn for readability.
  toFilterUnit?: (v: number) => number;
}

const COLUMNS: Column[] = [
  { key: "price", label: "Price", format: formatPrice },
  { key: "change_pct", label: "Chg %", format: formatPct },
  { key: "market_cap", label: "Mkt Cap (bn)", format: formatMarketCap, toFilterUnit: (v) => v / 1_000_000 },
  { key: "pe_ratio", label: "P/E", format: (v) => formatLiveRatio(v, 2, "x") },
  { key: "roe", label: "ROE %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "roa", label: "ROA %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "dividend_yield", label: "Div. Yield %", format: (v) => formatLiveRatio(v, 2, "%") },
  { key: "debt_to_equity", label: "D/E", format: formatMultiple },
  { key: "current_ratio", label: "Current Ratio", format: formatMultiple },
  { key: "net_profit_margin", label: "Net Margin %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "revenue_growth_yoy", label: "Rev Growth %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "eps_growth_yoy", label: "EPS Growth %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "ai_score", label: "AI Score", format: (v) => (v != null ? v.toFixed(1) : "—") },
];

interface RangeFilter {
  min: string;
  max: string;
}

const EMPTY_FILTERS: Record<SortKey, RangeFilter> = Object.fromEntries(
  COLUMNS.map((c) => [c.key, { min: "", max: "" }])
) as Record<SortKey, RangeFilter>;

const SIGNAL_STYLE: Record<string, string> = {
  strong_buy: "bg-[#10161A] text-[#DAE1EE] font-semibold",
  buy: "bg-[#10161A]/85 text-[#DAE1EE] font-medium",
  hold: "bg-[#B4C0D5]/40 text-[#566680] font-medium",
  sell: "bg-[#B4C0D5]/70 text-[#10161A] border border-[#8E9CB7]/50 font-medium",
  strong_sell: "bg-[#566680] text-[#DAE1EE] font-semibold",
  no_signal: "bg-white/60 text-[#8E9CB7]",
};

// Screening pool: 13 companies with financial data (3 verified + 10 unverified)
const SCREENING_POOL = new Set(["FFC", "EFERT", "FATIMA", "LUCK", "MLCF", "DGKC", "CHCC", "BWCL", "ACPL", "FCCL", "KOHC", "DCL", "GWLC"]);

function AiSignalCell({ row }: { row: ComparisonRow }) {
  if (!row.ai_signal && row.ai_score == null) {
    return <span className="text-xs text-muted">—</span>;
  }
  const style = SIGNAL_STYLE[row.ai_signal ?? "no_signal"] ?? "bg-surface-alt text-muted";
  return (
    <span
      title={row.score_disclaimer ?? undefined}
      className={`inline-flex cursor-help items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium ${style}`}
    >
      {row.ai_signal?.replace("_", " ") ?? "no signal"}
      {row.ai_score != null && <span className="opacity-70">· {row.ai_score.toFixed(1)}</span>}
      <Info size={9} className="opacity-50" />
    </span>
  );
}

export default function ScreenerTable({
  rows,
  mode = "screener",
}: {
  rows: ComparisonRow[];
  /** "ranking" defaults the sort to AI Score (desc) and adds a rank column. */
  mode?: "screener" | "ranking";
}) {
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState<string>("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [sortKey, setSortKey] = useState<SortKey | null>(mode === "ranking" ? "ai_score" : null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // rows arrive from SSR with price/change_pct/pe_ratio/dividend_yield null (fast,
  // DB-only -- see comparison.py's docstring); live quotes are merged in here once the
  // client-side scrape resolves, without blocking anything above this component.
  const { quotesBySymbol } = useLiveQuotes();
  const liveRows = useMemo(
    () => rows.map((r) => (r.symbol ? mergeLiveQuote(r, quotesBySymbol[r.symbol]) : r)),
    [rows, quotesBySymbol]
  );

  const sectors = useMemo(
    () => Array.from(new Set(liveRows.map((r) => r.sector).filter((s): s is string => !!s))).sort(),
    [liveRows]
  );

  const setFilter = (key: SortKey, bound: "min" | "max", value: string) => {
    setFilters((prev) => ({ ...prev, [key]: { ...prev[key], [bound]: value } }));
  };

  const handleSort = (key: SortKey) => {
    if (sortKey !== key) {
      setSortKey(key);
      setSortDirection("desc");
    } else if (sortDirection === "desc") {
      setSortDirection("asc");
    } else {
      setSortKey(null);
    }
  };

  const activeFilterCount = Object.values(filters).filter((f) => f.min !== "" || f.max !== "").length + (sector ? 1 : 0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let result = liveRows.filter(
      (r) => !q || r.name.toLowerCase().includes(q) || (r.symbol ?? "").toLowerCase().includes(q)
    );
    if (sector) result = result.filter((r) => r.sector === sector);

    for (const column of COLUMNS) {
      const { min, max } = filters[column.key];
      if (min === "" && max === "") continue;
      result = result.filter((row) => {
        const raw = row[column.key];
        if (raw == null) return false;
        const value = column.toFilterUnit ? column.toFilterUnit(raw) : raw;
        if (min !== "" && value < parseFloat(min)) return false;
        if (max !== "" && value > parseFloat(max)) return false;
        return true;
      });
    }

    if (sortKey) {
      result = [...result].sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        if (av == null && bv == null) return 0;
        if (av == null) return 1; // nulls always sink to the bottom, regardless of direction
        if (bv == null) return -1;
        return sortDirection === "asc" ? av - bv : bv - av;
      });
    }

    return result;
  }, [liveRows, query, sector, filters, sortKey, sortDirection]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex min-w-[220px] items-center gap-2 rounded-full border border-border bg-surface px-4 py-2">
          <Search size={15} className="text-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ticker or company name..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
          />
        </div>
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="rounded-full border border-border bg-surface px-3 py-2 text-xs text-foreground focus:outline-none"
        >
          <option value="">All sectors</option>
          {sectors.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        {(activeFilterCount > 0 || sortKey) && (
          <button
            onClick={() => {
              setFilters(EMPTY_FILTERS);
              setSector("");
              setSortKey(mode === "ranking" ? "ai_score" : null);
              setSortDirection("desc");
            }}
            className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-2 text-xs text-muted hover:text-foreground"
          >
            <RotateCcw size={12} /> Reset filters &amp; sort
          </button>
        )}
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 rounded-2xl border border-border bg-surface p-4 sm:grid-cols-4 lg:grid-cols-6">
        {COLUMNS.map((column) => (
          <div key={column.key}>
            <p className="mb-1 text-[10px] text-muted">{column.label}</p>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={filters[column.key].min}
                onChange={(e) => setFilter(column.key, "min", e.target.value)}
                placeholder="min"
                className="w-full min-w-0 rounded-md border border-border bg-surface-alt px-1.5 py-1 text-xs focus:outline-none"
              />
              <input
                type="number"
                value={filters[column.key].max}
                onChange={(e) => setFilter(column.key, "max", e.target.value)}
                placeholder="max"
                className="w-full min-w-0 rounded-md border border-border bg-surface-alt px-1.5 py-1 text-xs focus:outline-none"
              />
            </div>
          </div>
        ))}
      </div>

      <p className="mb-3 text-xs text-muted">
        {filtered.length} of {rows.length} companies
        {mode === "ranking" && " · AI Score is a research-only average of quality/growth/financial-health/valuation/momentum (0–100, higher is better); risk dimensions are excluded from the average since higher isn't uniformly better for those."}
      </p>

      <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted">
              {mode === "ranking" && <th className="px-4 py-3 font-medium">#</th>}
              <th className="px-4 py-3 font-medium">Company</th>
              {COLUMNS.map((column) => (
                <th key={column.key} className="px-4 py-3 font-medium">
                  <button
                    onClick={() => handleSort(column.key)}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    {column.label}
                    {sortKey === column.key ? (
                      sortDirection === "desc" ? (
                        <ArrowDown size={11} />
                      ) : (
                        <ArrowUp size={11} />
                      )
                    ) : (
                      <ArrowUpDown size={11} className="opacity-40" />
                    )}
                  </button>
                </th>
              ))}
              <th className="px-4 py-3 font-medium">AI Signal</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + (mode === "ranking" ? 3 : 2)} className="px-4 py-6 text-center text-xs text-muted">
                  No companies match these filters.
                </td>
              </tr>
            )}
            {filtered.map((row, i) => (
              <tr key={row.id} className="hover:bg-surface-alt/60">
                {mode === "ranking" && (
                  <td className="px-4 py-3 text-xs text-muted tabular-nums">{i + 1}</td>
                )}
                <td className="px-4 py-3">
                  <Link href={`/companies/${row.id}`} className="flex items-center gap-2">
                    {row.symbol && (
                      <span className="rounded-md bg-accent/15 px-1.5 py-0.5 text-[10px] font-semibold text-accent">
                        {row.symbol}
                      </span>
                    )}
                    <span className="font-medium hover:text-accent">{row.name}</span>
                  </Link>
                  <div className="mt-0.5 flex items-center gap-1.5">
                    {row.sector && <span className="text-[10px] text-muted">{row.sector}</span>}
                    <CoverageBadge status={row.coverage_status} />
                  </div>
                </td>
                {COLUMNS.map((column) => (
                  <td
                    key={column.key}
                    className={`px-4 py-3 ${
                      column.key === "change_pct" ? ((row.change_pct ?? 0) >= 0 ? "text-positive" : "text-negative") : ""
                    }`}
                  >
                    {column.format(row[column.key])}
                  </td>
                ))}
                <td className="px-4 py-3">
                  <AiSignalCell row={row} />
                </td>
                <td className="px-4 py-3">
                  {row.symbol && SCREENING_POOL.has(row.symbol) && (
                    <Link
                      href="/screening"
                      className="inline-flex items-center gap-1 rounded-md bg-accent/10 px-2 py-1 text-xs font-medium text-accent hover:bg-accent/20 transition-colors"
                    >
                      <Microscope className="h-3 w-3" />
                      Deep Analysis
                    </Link>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
