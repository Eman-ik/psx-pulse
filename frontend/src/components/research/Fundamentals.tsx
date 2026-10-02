"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";

type Fact = { id: number; line_item: string; period_end: string; value: number; unit: string; scope: string; source_document_id: number };
type Ratio = {
  key: string;
  name: string;
  category: string;
  unit: string;
  formula: string;
  period_end: string;
  value: number;
  input_fact_ids: number[];
};
type Source = { id: number; document_type: string; url: string | null; local_path: string | null };
type BalanceFlag = { period_end: string; total_assets: number; total_liabilities_plus_equity: number; diff_pct: number };
type Payload = { issuer: string; facts: Fact[]; ratios: Ratio[]; sources: Source[]; balance_sheet_flags: BalanceFlag[] };

const STATEMENTS: [string, [string, string][]][] = [
  [
    "Income statement",
    [
      ["revenue", "Revenue"],
      ["cost_of_sales", "Cost of sales"],
      ["gross_profit", "Gross profit"],
      ["operating_profit", "Operating profit"],
      ["finance_cost", "Finance cost"],
      ["profit_after_tax", "Profit after tax"],
    ],
  ],
  [
    "Balance sheet",
    [
      ["total_assets", "Total assets"],
      ["current_assets", "Current assets"],
      ["inventory", "Inventory"],
      ["trade_debts", "Trade debts"],
      ["cash_and_bank", "Cash and bank"],
      ["short_term_investments", "Short-term investments"],
      ["total_liabilities", "Total liabilities"],
      ["current_liabilities", "Current liabilities"],
      ["total_equity", "Total equity"],
    ],
  ],
  [
    "Cash flow and per share",
    [
      ["operating_cash_flow", "Operating cash flow"],
      ["dividends_paid_total", "Dividends paid"],
      ["eps", "Earnings per share"],
      ["dividend_per_share", "Dividend per share"],
    ],
  ],
];

const RATIO_GROUPS: [string, string][] = [
  ["profitability", "Profitability"],
  ["growth", "Growth"],
  ["leverage", "Leverage"],
  ["liquidity", "Liquidity"],
  ["efficiency", "Efficiency"],
  ["cash_flow", "Cash flow and dividends"],
];

const BALANCE_TOTALS = new Set(["total_assets", "total_liabilities", "total_equity"]);

const yearLabel = (periodEnd: string) =>
  new Date(`${periodEnd}T00:00:00`).toLocaleDateString(undefined, { month: "short", year: "numeric" });

function formatFact(f: Fact) {
  if (f.unit === "PKR_thousand") return (f.value / 1e6).toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  if (f.unit === "PKR") return `PKR ${f.value.toFixed(2)}`;
  return `${f.value.toLocaleString()} ${f.unit}`;
}

function formatRatio(r: Ratio) {
  if (r.unit === "percent") return `${r.value.toFixed(1)}%`;
  if (r.unit === "ratio") return `${r.value.toFixed(2)}×`;
  return r.value.toFixed(2);
}

function Table({ periods, children, firstHeader }: { periods: string[]; children: React.ReactNode; firstHeader: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-sm">
        <thead>
          <tr className="text-left text-muted">
            <th className="py-2 pr-4 font-medium">{firstHeader}</th>
            {periods.map((p) => (
              <th key={p} className="py-2 pl-3 text-right font-medium" title={`Period ending ${p}`}>
                {yearLabel(p)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Fundamentals({ symbol, api }: { symbol: string; api: string }) {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Ratio | null>(null);

  useEffect(() => {
    setData(null);
    setError(null);
    setSelected(null);
    fetch(`${api}/fundamentals/${encodeURIComponent(symbol)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setData)
      .catch(() => setError("Could not load financial statements."));
  }, [symbol, api]);

  if (error) {
    return (
      <p className="flex items-center gap-2 text-sm text-negative">
        <AlertCircle className="h-4 w-4" /> {error}
      </p>
    );
  }
  if (!data) {
    return (
      <p className="flex items-center gap-2 text-sm text-muted">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading statements…
      </p>
    );
  }
  if (data.facts.length === 0) {
    return (
      <>
        <p className="text-sm">No source-linked financial statements are on file for {symbol}.</p>
        <p className="mt-1 text-sm text-muted">
          Valuation, profitability and balance-sheet analysis appear here once statements are loaded with a link to the
          document they came from.
        </p>
      </>
    );
  }

  const factsById = new Map(data.facts.map((f) => [f.id, f]));
  const factAt = new Map(data.facts.map((f) => [`${f.line_item}|${f.period_end}`, f]));
  const periods = [...new Set(data.facts.map((f) => f.period_end))].sort();
  const flaggedPeriods = new Set(data.balance_sheet_flags.map((f) => f.period_end));
  const usesFlaggedBalance = (r: Ratio) =>
    r.input_fact_ids.some((id) => {
      const f = factsById.get(id);
      return f && BALANCE_TOTALS.has(f.line_item) && flaggedPeriods.has(f.period_end);
    });
  const inputs = (r: Ratio) =>
    r.input_fact_ids
      .map((id) => factsById.get(id))
      .filter((f): f is Fact => !!f)
      .map((f) => `${f.line_item} (${yearLabel(f.period_end)}) = ${formatFact(f)}${f.unit === "PKR_thousand" ? " bn" : ""}`);
  const anyFlaggedRatio = data.ratios.some(usesFlaggedBalance);
  const isLargeChange = (r: Ratio) => r.category === "growth" && Math.abs(r.value) > 100;
  const anyLargeChange = data.ratios.some(isLargeChange);
  const sourceById = new Map(data.sources.map((s) => [s.id, s]));
  const sourceLabel = (f: Fact) => {
    const s = sourceById.get(f.source_document_id);
    return `${f.scope} · ${s ? s.url ?? s.local_path : "source"}`;
  };

  return (
    <div className="space-y-8">
      <div className="space-y-1 text-sm">
        {data.sources.map((s) => (
          <p key={s.id}>
            <span className="text-muted">Source: </span>
            {s.url ? (
              <a href={s.url} className="underline" target="_blank" rel="noreferrer">
                {s.url}
              </a>
            ) : (
              s.local_path
            )}
            <span className="text-muted">
              {" "}
              ({s.document_type.endsWith("manual_entry")
                ? "figures entered by hand from this document"
                : s.document_type === "financials_snapshot"
                  ? "PSX company page annual table, standalone"
                  : "company filing on PSX; figures read from the statements and tied out"}
              )
            </span>
          </p>
        ))}
        <p className="text-xs text-muted">
          Annual, {[...new Set(data.facts.map((f) => f.scope))].join(" and ")} statements. Amounts in PKR billions unless marked.
          A dash means that figure has not been loaded from the sources on file for that year.
        </p>
      </div>

      {data.balance_sheet_flags.map((f) => (
        <div key={f.period_end} className="flex gap-2 rounded-lg border border-negative/40 bg-negative/10 p-4 text-sm text-negative">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            The {yearLabel(f.period_end)} balance sheet doesn&apos;t balance in the source: total assets{" "}
            {(f.total_assets / 1e6).toFixed(2)} bn vs liabilities plus equity {(f.total_liabilities_plus_equity / 1e6).toFixed(2)} bn
            ({f.diff_pct}% apart). Ratios that use these totals are marked †.
          </span>
        </div>
      ))}

      {STATEMENTS.map(([title, items]) => {
        const rows = items.filter(([key]) => periods.some((p) => factAt.has(`${key}|${p}`)));
        if (rows.length === 0) return null;
        return (
          <div key={title}>
            <h3 className="mb-2 font-semibold">{title}</h3>
            <Table periods={periods} firstHeader="Line item">
              {rows.map(([key, label]) => (
                <tr key={key} className="border-t border-border/50">
                  <td className="py-2 pr-4">{label}</td>
                  {periods.map((p) => {
                    const f = factAt.get(`${key}|${p}`);
                    return (
                      <td key={p} className="py-2 pl-3 text-right tabular-nums" title={f ? sourceLabel(f) : undefined}>
                        {f ? formatFact(f) : <span className="text-muted" title="Not loaded from the sources on file">—</span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </Table>
          </div>
        );
      })}

      {RATIO_GROUPS.map(([category, title]) => {
        const inGroup = data.ratios.filter((r) => r.category === category);
        const keys = [...new Set(inGroup.map((r) => r.key))];
        if (keys.length === 0) return null;
        return (
          <div key={category}>
            <h3 className="mb-2 font-semibold">{title}</h3>
            <Table periods={periods} firstHeader="Ratio">
              {keys.map((key) => {
                const series = inGroup.filter((r) => r.key === key);
                return (
                  <tr key={key} className="border-t border-border/50 align-top">
                    <td className="py-2 pr-4">
                      {series[0].name}
                      <div className="text-xs text-muted">{series[0].formula}</div>
                    </td>
                    {periods.map((p) => {
                      const r = series.find((s) => s.period_end === p);
                      if (!r) return <td key={p} className="py-2 pl-3 text-right text-muted">—</td>;
                      const isSelected = selected === r;
                      return (
                        <td key={p} className="py-2 pl-3 text-right tabular-nums">
                          <button
                            type="button"
                            onClick={() => setSelected(isSelected ? null : r)}
                            aria-pressed={isSelected}
                            aria-label={`${r.name} ${yearLabel(p)}: ${formatRatio(r)}. Show inputs`}
                            className={`rounded px-1 underline decoration-dotted underline-offset-4 hover:bg-accent/10 focus:outline-none focus:ring-2 focus:ring-accent ${
                              isSelected ? "bg-accent/15" : ""
                            }`}
                          >
                            {formatRatio(r)}
                            {usesFlaggedBalance(r) && <span className="text-negative">†</span>}
                            {isLargeChange(r) && <span className="text-negative" title="Change of more than 100% in one year">‡</span>}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </Table>
            {selected && selected.category === category && (
              <div className="mt-3 rounded-lg border border-border bg-background/50 p-4 text-sm" aria-live="polite">
                <p className="font-medium">
                  {selected.name}, {yearLabel(selected.period_end)}: {formatRatio(selected)}
                </p>
                <p className="mt-1 text-xs text-muted">{selected.formula}</p>
                <ul className="mt-2 space-y-1">
                  {inputs(selected).map((line) => (
                    <li key={line} className="tabular-nums">
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      })}

      <p className="text-xs text-muted">
        Every ratio is computed only from the figures above; select a value to see its inputs. ROA, ROE and turnover use
        the average of opening and closing balances, so their first year is blank.
        {anyFlaggedRatio && " † uses balance-sheet totals from a year where the source doesn't balance."}
        {anyLargeChange &&
          " ‡ A change of more than 100% in one year usually reflects a merger, acquisition or restatement rather than organic growth; check the company's announcements before comparing these years."}
      </p>
    </div>
  );
}
