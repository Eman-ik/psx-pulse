import { TriangleAlert, TrendingDown, TrendingUp } from "lucide-react";
import type { RiskSnapshot } from "@/lib/api";

const RISK_TONE: Record<RiskSnapshot["overall_risk"], string> = {
  LOW: "text-[#10161A] bg-[#B4C0D5]/50 border border-[#8E9CB7]/40",
  MODERATE: "text-[#10161A] bg-[#DAE1EE] border border-[#8E9CB7]/50",
  ELEVATED: "text-[#DAE1EE] bg-[#566680] border border-[#566680]",
  HIGH: "text-[#DAE1EE] bg-[#10161A] border border-[#10161A]",
};

function badgeTone(text: string) {
  const t = text.toUpperCase();
  if (t.includes("HIGH") || t.includes("STRESSED") || t.includes("UNKNOWN")) {
    return "text-[#DAE1EE] bg-[#10161A]";
  }
  if (t.includes("MODERATE") || t.includes("ELEVATED")) {
    return "text-[#10161A] bg-[#B4C0D5]/60 border border-[#8E9CB7]/40";
  }
  return "text-[#10161A] bg-white/80 border border-white";
}

export default function RiskPanel({ risk, isSample }: { risk: RiskSnapshot; isSample: boolean }) {
  const rows: [string, string][] = [
    ["Overall Risk", risk.overall_risk],
    ["Geopolitical", risk.geopolitical],
    ["Economy", risk.economy],
    ["IMF Program", risk.imf_program],
    ["Currency (PKR)", risk.currency_pkr],
  ];

  return (
    <div className="glass-light rounded-2xl p-5 relative overflow-hidden">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TriangleAlert size={16} className="text-[#10161A]" />
          <h3 className="font-bold text-[#10161A] tracking-tight">Macro &amp; Geopolitical Risk</h3>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-bold tracking-tight ${RISK_TONE[risk.overall_risk]}`}>
          {risk.overall_risk}
        </span>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-xl border border-white/60 bg-[#B4C0D5]/25 p-3 backdrop-blur-xs">
            <p className="mb-1.5 text-[11px] font-semibold text-[#566680] uppercase tracking-wider">{label}</p>
            <span className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${badgeTone(value)}`}>
              {value}
            </span>
          </div>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-white/50 bg-white/40 p-3.5">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-[#10161A]">
            <TrendingUp size={13} className="text-[#566680]" /> Key Positives
          </p>
          <ul className="space-y-1.5 text-xs text-[#566680]">
            {risk.key_positives.map((item) => (
              <li key={item} className="flex gap-2 items-start">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#10161A]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-white/50 bg-white/40 p-3.5">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-[#10161A]">
            <TrendingDown size={13} className="text-[#566680]" /> Key Negatives
          </p>
          <ul className="space-y-1.5 text-xs text-[#566680]">
            {risk.key_negatives.map((item) => (
              <li key={item} className="flex gap-2 items-start">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#566680]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="mt-4 text-[10px] text-[#566680]">
        As of {risk.as_of_date} · analyst-maintained snapshot
        {isSample ? " · sample data (backend snapshot unavailable)" : ""}
      </p>
    </div>
  );
}
