"use client";

import type { FinancialFactPoint } from "@/lib/api";

const INCOME_STATEMENT: { key: string; label: string }[] = [
  { key: "revenue", label: "Revenue (Net Sales)" },
  { key: "gross_profit", label: "Gross Profit" },
  { key: "ebit", label: "EBIT (Operating Profit)" },
  { key: "interest_expense", label: "Finance Cost / Interest" },
  { key: "profit_before_tax", label: "Profit Before Tax" },
  { key: "taxation", label: "Taxation" },
  { key: "profit_after_tax", label: "Profit After Tax (PAT)" },
  { key: "eps", label: "EPS (PKR / share)" },
];

const BALANCE_SHEET: { key: string; label: string }[] = [
  { key: "total_assets", label: "Total Assets" },
  { key: "current_assets", label: "Current Assets" },
  { key: "current_liabilities", label: "Current Liabilities" },
  { key: "total_liabilities", label: "Total Liabilities" },
  { key: "total_equity", label: "Total Equity" },
  { key: "long_term_debt", label: "Long-term Debt" },
];

const CASH_FLOW: { key: string; label: string }[] = [
  { key: "operating_cash_flow", label: "Operating Cash Flow" },
  { key: "capital_expenditure", label: "Capital Expenditure" },
  { key: "free_cash_flow", label: "Free Cash Flow" },
  { key: "dividends_paid", label: "Dividends Paid" },
];

function fmtValue(v: number, unit: string): string {
  if (unit === "PKR" || unit === "PKR_per_share") return `PKR ${v.toFixed(2)}`;
  if (unit === "PKR_thousand" || unit === "PKR_000") {
    const bn = Math.abs(v) / 1_000_000;
    const sign = v < 0 ? "−" : "";
    return bn >= 1 ? `${sign}${bn.toFixed(1)} bn` : `${sign}${(Math.abs(v) / 1_000).toFixed(0)} mn`;
  }
  if (unit === "percent") return `${v.toFixed(1)}%`;
  return v.toFixed(2);
}

interface StatementTableProps {
  title: string;
  rows: { key: string; label: string }[];
  financials: Record<string, FinancialFactPoint[]>;
}

function StatementTable({ title, rows, financials }: StatementTableProps) {
  // Collect all annual period_ends across all relevant rows
  const periodSet = new Set<string>();
  for (const { key } of rows) {
    (financials[key] ?? [])
      .filter((f) => f.period_type === "annual")
      .forEach((f) => periodSet.add(f.period_end));
  }
  const periods = Array.from(periodSet).sort().slice(-6); // last 6 years

  // Only include rows that have at least one value in these periods
  const activeRows = rows.filter(({ key }) => {
    const points = financials[key] ?? [];
    return points.some((f) => f.period_type === "annual" && periods.includes(f.period_end));
  });

  if (activeRows.length === 0 || periods.length === 0) return null;

  // Build lookup: key -> period_end -> point
  const lookup: Record<string, Record<string, FinancialFactPoint>> = {};
  for (const { key } of activeRows) {
    lookup[key] = {};
    for (const f of financials[key] ?? []) {
      if (f.period_type === "annual") lookup[key][f.period_end] = f;
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <h4 className="mb-3 text-sm font-semibold">{title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2 pr-4 text-left font-normal text-muted">Line Item</th>
              {periods.map((p) => (
                <th key={p} className="py-2 px-3 text-right font-medium tabular-nums">
                  {p.slice(0, 4)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {activeRows.map(({ key, label }) => (
              <tr key={key} className="border-b border-border/40 last:border-0 hover:bg-surface-alt/50">
                <td className="py-2 pr-4 text-muted">{label}</td>
                {periods.map((p) => {
                  const pt = lookup[key]?.[p];
                  return (
                    <td key={p} className="py-2 px-3 text-right tabular-nums">
                      {pt != null ? fmtValue(pt.value, pt.unit) : <span className="text-muted/40">—</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[10px] text-muted">PKR bn/mn values in PKR thousands source. Periods = fiscal year-end date.</p>
    </div>
  );
}

export default function FinancialStatementsPanel({
  financials,
}: {
  financials: Record<string, FinancialFactPoint[]>;
}) {
  return (
    <div className="flex flex-col gap-5 mt-6">
      <StatementTable title="Income Statement" rows={INCOME_STATEMENT} financials={financials} />
      <StatementTable title="Balance Sheet" rows={BALANCE_SHEET} financials={financials} />
      <StatementTable title="Cash Flow Statement" rows={CASH_FLOW} financials={financials} />
    </div>
  );
}
