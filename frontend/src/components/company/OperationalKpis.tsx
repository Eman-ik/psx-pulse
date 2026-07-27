"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CompanyOverview } from "@/lib/api";

const METRIC_LABELS: Record<string, string> = {
  capacity_utilization_pct: "Capacity Utilization",
  "production_volume::urea": "Urea Production",
  "production_volume::fertilizer_total": "Total Production",
  "sales_volume::urea": "Urea Sales Volume",
  "sales_volume::dap_imported": "Imported DAP Sales Volume",
  "sales_volume::fertilizer_total": "Total Sales Volume",
  "market_share_pct::urea": "Urea Market Share",
  "market_share_pct::fertilizer_production": "Production Market Share",
  "market_share_pct::fertilizer_offtake": "Offtake Market Share",
  "nameplate_capacity::fertilizer_total": "Nameplate Capacity",
  "product_mix_pct::np": "Product Mix — NP",
  "product_mix_pct::urea": "Product Mix — Urea",
  "product_mix_pct::can": "Product Mix — CAN",
};

export default function OperationalKpis({ metrics }: { metrics: CompanyOverview["operational_metrics"] }) {
  const entries = Object.entries(metrics);
  if (entries.length === 0) {
    return <p className="text-xs text-muted">No structured operational/production data on file yet.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {entries.map(([key, series]) => {
        const chartData = series.map((p) => ({ year: p.period_end.slice(0, 4), value: p.value }));
        const latest = series[series.length - 1];
        return (
          <div key={key} className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">{METRIC_LABELS[key] ?? key}</p>
            <p className="mb-2 text-lg font-semibold">
              {latest.value.toLocaleString()} <span className="text-xs font-normal text-muted">{latest.unit}</span>
            </p>
            {chartData.length > 1 && (
              <div className="h-20 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="year" tick={{ fill: "#8b92a5", fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, fontSize: 11 }}
                    />
                    <Bar dataKey="value" fill="#4f7cff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
