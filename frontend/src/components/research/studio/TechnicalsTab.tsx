"use client";

import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { type Freshness, useStudio } from "@/lib/studio-api";
import { Card, day, ErrorNote, Label, Loading, Missing, num, pct, Row, tone } from "./ui";

type Indicators = {
  price: number;
  bars_available: number;
  price_vs_20dma: number | null;
  price_vs_50dma: number | null;
  price_vs_200dma: number | null;
  rsi: number | null;
  volume_vs_avg: number | null;
  lookback_days: number;
  lookback_complete: boolean;
  lookback_high: number;
  lookback_low: number;
};
type Relative = { status: string; horizons?: Record<string, { stock: number | null; index: number | null }> };
type Technicals = {
  freshness: Freshness;
  indicators: Indicators | null;
  series: { adjusted: boolean; adjustment_note: string; bars: { date: string; close: number; volume: number | null }[] };
  liquidity: {
    average_volume_20d: number | null;
    approx_value_traded_20d_pkr: number | null;
    approx_value_note: string;
    zero_volume_days_in_window: number;
    window_days: number;
  };
  relative_performance: Record<string, Relative>;
};

const NA = "Not enough price history";
const HORIZON_LABEL: Record<string, string> = { "1m": "1 month", "3m": "3 months", "6m": "6 months", "12m": "12 months" };

export function TechnicalsTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Technicals>(symbol, "technicals?bars=252");
  if (loading) return <Loading what="Loading price history" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const { indicators: ind, series, liquidity } = data;
  const bars = series.bars;

  return (
    <div className="space-y-6">
      {data.freshness.stale && <ErrorNote message={`Prices are stale: the latest close on file is ${day(data.freshness.as_of)}.`} />}

      <Card title="Price and volume" aside={<span className="flex gap-2"><Label kind={data.freshness.stale ? "STALE" : "DELAYED"} /><Label kind="VERIFIED" /></span>}>
        {bars.length < 2 ? (
          <Missing>No price history on file.</Missing>
        ) : (
          <div className="h-72 w-full" role="img" aria-label={`Closing price and volume chart for ${symbol}, ${bars.length} sessions`}>
            <ResponsiveContainer>
              <ComposedChart data={bars} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid strokeOpacity={0.15} vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={48} tickFormatter={(d: string) => day(d)} />
                <YAxis yAxisId="p" domain={["auto", "auto"]} tick={{ fontSize: 11 }} width={52} />
                <YAxis yAxisId="v" orientation="right" hide domain={[0, (max: number) => max * 4]} />
                <Tooltip
                  contentStyle={{ background: "var(--surface, #fff)", border: "1px solid var(--border, #ccc)", fontSize: 12 }}
                  formatter={(v, name) => [typeof v === "number" ? v.toLocaleString() : v, name === "close" ? "Close (PKR)" : "Volume"]}
                  labelFormatter={(d) => day(String(d))}
                />
                <Bar yAxisId="v" dataKey="volume" fill="currentColor" fillOpacity={0.15} isAnimationActive={false} />
                <Line yAxisId="p" dataKey="close" stroke="var(--accent, #2563eb)" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                {ind && <ReferenceLine yAxisId="p" y={ind.lookback_high} strokeDasharray="4 4" strokeOpacity={0.5} />}
                {ind && <ReferenceLine yAxisId="p" y={ind.lookback_low} strokeDasharray="4 4" strokeOpacity={0.5} />}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
        <p className="mt-3 text-xs text-muted">{series.adjustment_note} Dashed lines mark the high and low of the {ind?.lookback_days ?? bars.length}-day window shown.</p>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Indicators" aside={<Label kind="DERIVED" />}>
          {!ind ? (
            <Missing>No close on the latest market date, so indicators can&apos;t be computed.</Missing>
          ) : (
            <>
              {(
                [["vs 20-day average", ind.price_vs_20dma], ["vs 50-day average", ind.price_vs_50dma], ["vs 200-day average", ind.price_vs_200dma]] as const
              ).map(([label, v]) => (
                <Row key={label} label={label}>
                  {v == null ? <span className="text-muted" title={NA}>—</span> : <span className={tone(v)}>{pct(v)}</span>}
                </Row>
              ))}
              <Row label="RSI (14-day)">{ind.rsi == null ? <span className="text-muted" title={NA}>—</span> : num(ind.rsi, 1)}</Row>
              <Row label="Volume vs prior 20-day average">{ind.volume_vs_avg == null ? "—" : `${num(ind.volume_vs_avg)}×`}</Row>
              <Row label={ind.lookback_complete ? "52-week range" : `${ind.lookback_days}-day range`}>
                {num(ind.lookback_low)} to {num(ind.lookback_high)}
              </Row>
              <p className="mt-2 text-xs text-muted">
                {ind.bars_available} closes on file. An indicator that needs more history than that is blank, not zero.
              </p>
            </>
          )}
        </Card>

        <Card title="Liquidity" aside={<Label kind="DERIVED" />}>
          <Row label="Average volume (20 days)">{liquidity.average_volume_20d == null ? "—" : liquidity.average_volume_20d.toLocaleString()}</Row>
          <Row label="Approx. value traded per day">
            {liquidity.approx_value_traded_20d_pkr == null ? "—" : `PKR ${liquidity.approx_value_traded_20d_pkr.toLocaleString()}`}
          </Row>
          <Row label="Zero-volume days">{liquidity.zero_volume_days_in_window} of {liquidity.window_days}</Row>
          <p className="mt-2 text-xs text-muted">{liquidity.approx_value_note}</p>
        </Card>
      </div>

      <Card title="Performance relative to indices" aside={<Label kind="DERIVED" />}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="text-left text-muted">
                <th className="py-2 font-medium">Horizon</th>
                <th className="py-2 text-right font-medium">Stock</th>
                {Object.keys(data.relative_performance).map((code) => (
                  <th key={code} className="py-2 text-right font-medium">{code} / excess</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.keys(HORIZON_LABEL).map((h) => {
                const stock = Object.values(data.relative_performance).find((r) => r.horizons)?.horizons?.[h]?.stock ?? null;
                return (
                  <tr key={h} className="border-t border-border/50">
                    <td className="py-2">{HORIZON_LABEL[h]}</td>
                    <td className={`py-2 text-right tabular-nums ${tone(stock)}`}>{pct(stock)}</td>
                    {Object.values(data.relative_performance).map((r, i) => {
                      const cell = r.horizons?.[h];
                      const excess = cell && cell.stock != null && cell.index != null ? cell.stock - cell.index : null;
                      return (
                        <td key={i} className="py-2 text-right tabular-nums">
                          {r.status !== "AVAILABLE" || !cell ? "—" : <>{pct(cell.index)} <span className={tone(excess)}>({pct(excess, 1)})</span></>}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">
          Price returns only, aligned to the same dates. FERTIX and CEMENTIX are equal-weighted indices computed from the sector&apos;s
          own stocks, not published PSX indices. A blank means no close within 7 days of the lookback date.
        </p>
      </Card>
    </div>
  );
}
