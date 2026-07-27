"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FinancialFactPoint } from "@/lib/api";

interface FinancialsChartProps {
  revenue?: FinancialFactPoint[];
  profitAfterTax?: FinancialFactPoint[];
  eps?: FinancialFactPoint[];
}

export default function FinancialsChart({ revenue, profitAfterTax, eps }: FinancialsChartProps) {
  const years = new Set<string>();
  revenue?.forEach((r) => years.add(r.period_end));
  profitAfterTax?.forEach((r) => years.add(r.period_end));

  const revenueByYear = Object.fromEntries((revenue ?? []).map((r) => [r.period_end, r.value]));
  const patByYear = Object.fromEntries((profitAfterTax ?? []).map((r) => [r.period_end, r.value]));

  const data = Array.from(years)
    .sort()
    .map((period_end) => ({
      year: period_end.slice(0, 4),
      revenue: revenueByYear[period_end] != null ? revenueByYear[period_end] / 1_000_000 : null,
      pat: patByYear[period_end] != null ? patByYear[period_end] / 1_000_000 : null,
    }));

  const epsData = (eps ?? [])
    .slice()
    .sort((a, b) => a.period_end.localeCompare(b.period_end))
    .map((e) => ({ year: e.period_end.slice(0, 4), eps: e.value }));

  if (data.length === 0 && epsData.length === 0) {
    return <p className="text-xs text-muted">No financial time series available for this company yet.</p>;
  }

  const scopes = new Set([...(revenue ?? []), ...(profitAfterTax ?? [])].map((r) => r.scope));
  const units = new Set([...(revenue ?? []), ...(profitAfterTax ?? [])].map((r) => r.unit));

  return (
    <div className="flex flex-col gap-2">
      {(scopes.size > 0 || units.size > 0) && (
        <p className="text-[10px] text-muted">
          Scope: {scopes.size > 0 ? [...scopes].join(", ") : "—"} · Unit: {units.size > 0 ? [...units].join(", ") : "—"}
          {scopes.size > 1 && " — mixed scope across years, compare with care"}
        </p>
      )}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
      {data.length > 0 && (
        <div className="h-56 w-full">
          <p className="mb-1 text-xs text-muted">Revenue &amp; Profit After Tax (PKR bn)</p>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4f7cff" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#4f7cff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="patFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: "#8b92a5", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#8b92a5", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                labelStyle={{ color: "#8b92a5" }}
              />
              <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#4f7cff" strokeWidth={2} fill="url(#revFill)" connectNulls />
              <Area type="monotone" dataKey="pat" name="Profit After Tax" stroke="#22c55e" strokeWidth={2} fill="url(#patFill)" connectNulls />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {epsData.length > 0 && (
        <div className="h-56 w-full">
          <p className="mb-1 text-xs text-muted">EPS (PKR)</p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={epsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: "#8b92a5", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#8b92a5", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                labelStyle={{ color: "#8b92a5" }}
              />
              <Bar dataKey="eps" name="EPS" fill="#ffcd4b" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      </div>
    </div>
  );
}
