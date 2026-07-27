"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDown, ArrowUp, ArrowUpDown, Lock, RotateCcw, Search } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatLiveRatio, formatMarketCap, formatMultiple, formatPct, formatPercent, formatPrice } from "@/lib/format";

type SortKey = "price" | "change_pct" | "market_cap" | "pe_ratio" | "roe" | "dividend_yield" | "debt_to_equity";
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
  { key: "market_cap", label: "Market Cap (bn)", format: formatMarketCap, toFilterUnit: (v) => v / 1_000_000 },
  { key: "pe_ratio", label: "P/E", format: (v) => formatLiveRatio(v, 2, "x") },
  { key: "roe", label: "ROE %", format: (v) => (v != null ? formatPercent(v) : "—") },
  { key: "dividend_yield", label: "Div. Yield %", format: (v) => formatLiveRatio(v, 2, "%") },
  { key: "debt_to_equity", label: "D/E", format: formatMultiple },
];

interface RangeFilter {
  min: string;
  max: string;
}

const EMPTY_FILTERS: Record<SortKey, RangeFilter> = {
  price: { min: "", max: "" },
  change_pct: { min: "", max: "" },
  market_cap: { min: "", max: "" },
  pe_ratio: { min: "", max: "" },
  roe: { min: "", max: "" },
  dividend_yield: { min: "", max: "" },
  debt_to_equity: { min: "", max: "" },
};

export default function ScreenerTable({ rows }: { rows: ComparisonRow[] }) {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

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

  const activeFilterCount = Object.values(filters).filter((f) => f.min !== "" || f.max !== "").length;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let result = rows.filter(
      (r) => !q || r.name.toLowerCase().includes(q) || (r.symbol ?? "").toLowerCase().includes(q)
    );

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
  }, [rows, query, filters, sortKey, sortDirection]);

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
        {(activeFilterCount > 0 || sortKey) && (
          <button
            onClick={() => {
              setFilters(EMPTY_FILTERS);
              setSortKey(null);
            }}
            className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-2 text-xs text-muted hover:text-foreground"
          >
            <RotateCcw size={12} /> Reset filters &amp; sort
          </button>
        )}
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 rounded-2xl border border-border bg-surface p-4 sm:grid-cols-4 lg:grid-cols-7">
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
      </p>

      <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted">
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
              <th className="px-4 py-3 font-medium">
                <span className="inline-flex items-center gap-1">
                  <Lock size={11} /> AI Signal
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 2} className="px-4 py-6 text-center text-xs text-muted">
                  No companies match these filters.
                </td>
              </tr>
            )}
            {filtered.map((row) => (
              <tr key={row.id} className="hover:bg-surface-alt/60">
                <td className="px-4 py-3">
                  <Link href={`/companies/${row.id}`} className="flex items-center gap-2">
                    {row.symbol && (
                      <span className="rounded-md bg-accent/15 px-1.5 py-0.5 text-[10px] font-semibold text-accent">
                        {row.symbol}
                      </span>
                    )}
                    <span className="font-medium hover:text-accent">{row.name}</span>
                  </Link>
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
                  <span
                    title="AI signal output is built but hidden pending SECP/PSX compliance review — not a fabricated rating."
                    className="inline-flex cursor-help items-center gap-1 rounded-full bg-surface-alt px-2 py-1 text-[10px] font-medium text-muted"
                  >
                    <Lock size={10} /> Locked
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
