"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { CompanySummary } from "@/lib/types";

export const DONUT_COLORS = ["#4f7cff", "#ff4d9d", "#ffcd4b", "#22c55e"];
const COLORS = DONUT_COLORS;

export default function MarketCapDonut({ companies }: { companies: CompanySummary[] }) {
  const data = companies.map((c) => ({ name: c.symbol, value: c.marketCapPkrBn }));

  return (
    <div className="relative h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={45}
            outerRadius={65}
            paddingAngle={3}
            strokeWidth={0}
          >
            {data.map((entry, i) => (
              <Cell key={entry.name} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#161a26",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12,
              fontSize: 12,
            }}
            formatter={(value, name) => [`PKR ${value} bn`, name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-[10px] text-muted">by mkt cap</p>
      </div>
    </div>
  );
}
