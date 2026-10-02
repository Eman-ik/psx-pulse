"use client";

import { useStudio } from "@/lib/studio-api";
import { Card, ErrorNote, Loading, num, pct, tone } from "./ui";

type Cell = { value: number; period_end: string } | null;
type Peers = {
  peer_selection: { method: string; sector: string | null; count: number };
  return_percentiles: Record<string, number | null>;
  rows: {
    symbol: string;
    name: string;
    is_subject: boolean;
    close: number | null;
    returns: Record<string, number | null>;
    rsi: number | null;
    fundamentals: Record<string, Cell>;
  }[];
  note: string;
};

const RETURNS = [["1m", "1M"], ["3m", "3M"], ["6m", "6M"], ["12m", "12M"]] as const;
const RATIOS = [["net_profit_margin", "Net margin %"], ["roe", "ROE %"], ["revenue_growth_yoy", "Rev. growth %"], ["debt_to_equity", "Liab./equity ×"], ["current_ratio", "Current ratio ×"]] as const;

export function PeersTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Peers>(symbol, "peers");
  if (loading) return <Loading what="Comparing peers" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const subject = data.rows.find((r) => r.is_subject);

  return (
    <div className="space-y-6">
      <Card title={`Peer set: ${data.peer_selection.sector ?? "no sector on file"} (${data.peer_selection.count})`}>
        <p className="text-sm text-muted">{data.peer_selection.method}</p>
        {subject && (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {RETURNS.map(([k, label]) => (
              <div key={k} className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted">{label} return rank</p>
                <p className="text-lg font-bold">{data.return_percentiles[k] == null ? "—" : `${data.return_percentiles[k]}th percentile`}</p>
              </div>
            ))}
          </div>
        )}
        <p className="mt-2 text-xs text-muted">Percentile within this peer set, price returns only. Shown when at least 3 peers have a value.</p>
      </Card>

      <Card title="Returns and statements side by side">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="text-left text-muted">
                <th className="py-2 pr-3 font-medium">Company</th>
                <th className="py-2 text-right font-medium">Close</th>
                {RETURNS.map(([, l]) => <th key={l} className="py-2 text-right font-medium">{l}</th>)}
                <th className="py-2 text-right font-medium">RSI</th>
                {RATIOS.map(([, l]) => <th key={l} className="py-2 text-right font-medium">{l}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.symbol} className={`border-t border-border/50 ${r.is_subject ? "bg-accent/10 font-medium" : ""}`}>
                  <td className="py-2 pr-3"><span className="font-semibold">{r.symbol}</span><span className="block text-xs font-normal text-muted">{r.name}</span></td>
                  <td className="py-2 text-right tabular-nums">{num(r.close)}</td>
                  {RETURNS.map(([k]) => <td key={k} className={`py-2 text-right tabular-nums ${tone(r.returns[k])}`}>{pct(r.returns[k], 1)}</td>)}
                  <td className="py-2 text-right tabular-nums">{num(r.rsi, 1)}</td>
                  {RATIOS.map(([k]) => {
                    const c = r.fundamentals[k];
                    return (
                      <td key={k} className="py-2 text-right tabular-nums" title={c ? `Period ending ${c.period_end}` : "No source-linked statements on file"}>
                        {c ? num(c.value, 1) : <span className="text-muted">N/A</span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">{data.note}</p>
      </Card>
    </div>
  );
}
