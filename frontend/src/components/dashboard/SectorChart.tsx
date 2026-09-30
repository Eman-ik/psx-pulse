"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IndexPoint } from "@/lib/types";

export default function SectorChart({ data }: { data: IndexPoint[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="sectorFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8E9CB7" stopOpacity={0.35} />
              <stop offset="60%" stopColor="#B4C0D5" stopOpacity={0.12} />
              <stop offset="100%" stopColor="#DAE1EE" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="kseFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#566680" stopOpacity={0.18} />
              <stop offset="100%" stopColor="#566680" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(86, 102, 128, 0.12)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#566680", fontSize: 11, fontWeight: 500 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#566680", fontSize: 11, fontWeight: 500 }}
            axisLine={false}
            tickLine={false}
            domain={["dataMin - 2", "dataMax + 2"]}
          />
          <Tooltip
            contentStyle={{
              background: "#10161A",
              border: "1px solid rgba(142, 156, 183, 0.35)",
              borderRadius: 12,
              fontSize: 12,
              color: "#DAE1EE",
              boxShadow: "0 14px 30px rgba(16, 22, 26, 0.35)",
            }}
            labelStyle={{ color: "#B4C0D5", fontWeight: 600 }}
          />
          <Area
            type="monotone"
            dataKey="sectorIndex"
            name="Fertilizer Sector Index (FERTIX)"
            stroke="#10161A"
            strokeWidth={2.2}
            fill="url(#sectorFill)"
          />
          <Area
            type="monotone"
            dataKey="kse100Index"
            name="KSE-100 Benchmark"
            stroke="#566680"
            strokeWidth={1.8}
            strokeDasharray="4 3"
            fill="url(#kseFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
