import { Lock } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatLiveRatio, formatMarketCap, formatMultiple, formatPct, formatPercent, formatPrice } from "@/lib/format";

function rankLine(rows: ComparisonRow[], issuerId: number, key: keyof ComparisonRow, label: string) {
  const ranked = rows
    .filter((r) => r[key] != null)
    .sort((a, b) => (b[key] as number) - (a[key] as number));
  const position = ranked.findIndex((r) => r.id === issuerId);
  if (position === -1) return null;
  return `${label} ranks ${position + 1} of ${ranked.length} in Fertilizer coverage`;
}

export default function CompetitorsTab({ rows, issuerId }: { rows: ComparisonRow[]; issuerId: number }) {
  if (rows.length === 0) {
    return <p className="text-xs text-muted">Peer comparison data unavailable — backend unreachable.</p>;
  }

  const roeLine = rankLine(rows, issuerId, "roe", "ROE");
  const peLine = rankLine(rows, issuerId, "market_cap", "Market cap");

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted">
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">Price</th>
              <th className="px-4 py-3 font-medium">Chg %</th>
              <th className="px-4 py-3 font-medium">Market Cap</th>
              <th className="px-4 py-3 font-medium">P/E</th>
              <th className="px-4 py-3 font-medium">ROE</th>
              <th className="px-4 py-3 font-medium">Div. Yield</th>
              <th className="px-4 py-3 font-medium">D/E</th>
              <th className="px-4 py-3 font-medium">
                <span className="inline-flex items-center gap-1">
                  <Lock size={11} /> AI Signal
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => {
              const isYou = row.id === issuerId;
              return (
                <tr key={row.id} className={isYou ? "bg-accent/5" : undefined}>
                  <td className="px-4 py-3">
                    <span className="font-medium">{row.symbol ?? row.name}</span>
                    {isYou && (
                      <span className="ml-2 rounded-full bg-accent/15 px-2 py-0.5 text-[10px] font-semibold text-accent">
                        You
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">{formatPrice(row.price)}</td>
                  <td className={`px-4 py-3 ${(row.change_pct ?? 0) >= 0 ? "text-positive" : "text-negative"}`}>
                    {formatPct(row.change_pct)}
                  </td>
                  <td className="px-4 py-3">{formatMarketCap(row.market_cap)}</td>
                  <td className="px-4 py-3">{formatLiveRatio(row.pe_ratio, 2, "x")}</td>
                  <td className="px-4 py-3">{row.roe != null ? formatPercent(row.roe) : "—"}</td>
                  <td className="px-4 py-3">{formatLiveRatio(row.dividend_yield, 2, "%")}</td>
                  <td className="px-4 py-3">{formatMultiple(row.debt_to_equity)}</td>
                  <td className="px-4 py-3">
                    <span
                      title="AI signal output is built but hidden pending SECP/PSX compliance review — not a fabricated rating."
                      className="inline-flex cursor-help items-center gap-1 rounded-full bg-surface-alt px-2 py-1 text-[10px] font-medium text-muted"
                    >
                      <Lock size={10} /> Locked
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {(roeLine || peLine) && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h3 className="mb-2 font-semibold">Relative Position</h3>
          <ul className="space-y-1 text-xs text-muted">
            {roeLine && <li>{roeLine}</li>}
            {peLine && <li>{peLine}</li>}
          </ul>
          <p className="mt-3 text-[10px] text-muted">
            Factual ranking against covered Fertilizer peers only — not an AI interpretation.
          </p>
        </div>
      )}
    </div>
  );
}
