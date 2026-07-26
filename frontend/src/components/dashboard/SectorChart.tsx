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
              <stop offset="0%" stopColor="#4f7cff" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#4f7cff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="kseFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff4d9d" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#ff4d9d" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#8b92a5", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#8b92a5", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            domain={["dataMin - 2", "dataMax + 2"]}
          />
          <Tooltip
            contentStyle={{
              background: "#161a26",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12,
              fontSize: 12,
            }}
            labelStyle={{ color: "#8b92a5" }}
          />
          <Area
            type="monotone"
            dataKey="sectorIndex"
            name="Fertilizer Sector Index"
            stroke="#4f7cff"
            strokeWidth={2}
            fill="url(#sectorFill)"
          />
          <Area
            type="monotone"
            dataKey="kse100Index"
            name="KSE-100"
            stroke="#ff4d9d"
            strokeWidth={2}
            fill="url(#kseFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
