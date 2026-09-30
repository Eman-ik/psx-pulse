"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { CompanySummary } from "@/lib/types";

export const DONUT_COLORS = [
  "#10161A", /* Black Is Back */
  "#566680", /* Dana */
  "#8E9CB7", /* Periwinkle Blossom */
  "#B4C0D5", /* Movie Magic */
  "#3A4B62", /* Deep Slate */
  "#6E7E99", /* Muted Periwinkle */
  "#A3B1C9", /* Soft Mist */
];
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
            strokeWidth={1.5}
            stroke="#DAE1EE"
          >
            {data.map((entry, i) => (
              <Cell key={entry.name} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#10161A",
              border: "1px solid rgba(142, 156, 183, 0.35)",
              borderRadius: 12,
              fontSize: 12,
              color: "#DAE1EE",
              boxShadow: "0 14px 30px rgba(16, 22, 26, 0.35)",
            }}
            formatter={(value, name) => [`PKR ${value} bn`, name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-[10px] uppercase font-mono tracking-wider text-[#566680]">by mkt cap</p>
      </div>
    </div>
  );
}
