import { TriangleAlert, TrendingDown, TrendingUp } from "lucide-react";
import type { SectorRiskSnapshot } from "@/lib/types";

const RISK_TONE: Record<SectorRiskSnapshot["overallRisk"], string> = {
  LOW: "text-positive bg-positive/10",
  MODERATE: "text-accent-yellow bg-accent-yellow/10",
  ELEVATED: "text-accent-yellow bg-accent-yellow/10",
  HIGH: "text-negative bg-negative/10",
};

function badgeTone(text: string) {
  const t = text.toUpperCase();
  if (t.includes("HIGH") || t.includes("STRESSED") || t.includes("UNKNOWN")) return "text-negative bg-negative/10";
  if (t.includes("MODERATE") || t.includes("ELEVATED")) return "text-accent-yellow bg-accent-yellow/10";
  return "text-positive bg-positive/10";
}

export default function RiskPanel({ risk }: { risk: SectorRiskSnapshot }) {
  const rows: [string, string][] = [
    ["Overall Risk", risk.overallRisk],
    ["Geopolitical", risk.geopolitical],
    ["Economy", risk.economy],
    ["IMF Program", risk.imfProgram],
    ["Currency (PKR)", risk.currencyPkr],
  ];

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TriangleAlert size={16} className="text-negative" />
          <h3 className="font-semibold">Macro &amp; Geopolitical Risk</h3>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${RISK_TONE[risk.overallRisk]}`}>
          {risk.overallRisk}
        </span>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-surface-alt p-3">
            <p className="mb-1.5 text-[11px] text-muted">{label}</p>
            <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${badgeTone(value)}`}>
              {value}
            </span>
          </div>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-positive">
            <TrendingUp size={13} /> Key Positives
          </p>
          <ul className="space-y-1.5 text-xs text-muted">
            {risk.keyPositives.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-positive" />
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-negative">
            <TrendingDown size={13} /> Key Negatives
          </p>
          <ul className="space-y-1.5 text-xs text-muted">
            {risk.keyNegatives.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-negative" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="mt-4 text-[10px] text-muted">
        As of {risk.asOfDate} · analyst-maintained snapshot, sample data for this pilot build
      </p>
    </div>
  );
}
