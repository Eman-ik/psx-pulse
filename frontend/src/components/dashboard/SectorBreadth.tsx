import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { CompanySummary } from "@/lib/types";

export default function SectorBreadth({ companies, totalVolume }: { companies: CompanySummary[]; totalVolume: number | null }) {
  const advancers = companies.filter((c) => c.changePct > 0);
  const decliners = companies.filter((c) => c.changePct < 0);
  const unchanged = companies.filter((c) => c.changePct === 0);
  const total = companies.length || 1;

  const sorted = [...companies].sort((a, b) => b.changePct - a.changePct);
  const topGainer = sorted[0];
  const topLoser = sorted[sorted.length - 1];

  const rows: [string, number, string, typeof ArrowUp][] = [
    ["Advancers", advancers.length, "bg-positive", ArrowUp],
    ["Decliners", decliners.length, "bg-negative", ArrowDown],
    ["Unchanged", unchanged.length, "bg-muted", Minus],
  ];

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Fertilizer Sector Breadth</h3>
        <span className="text-xs text-muted">{companies.length} names</span>
      </div>

      <div className="mb-4 flex flex-col gap-3">
        {rows.map(([label, count, color, Icon]) => (
          <div key={label} className="flex items-center gap-3">
            <Icon size={13} className="text-muted" />
            <span className="w-20 text-xs text-muted">{label}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-alt">
              <div className={`h-full rounded-full ${color}`} style={{ width: `${(count / total) * 100}%` }} />
            </div>
            <span className="w-5 text-right text-xs font-medium">{count}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-border pt-4 text-xs">
        <div>
          <p className="mb-1 text-muted">Top Gainer</p>
          <p className="font-medium text-positive">
            {topGainer.symbol} +{topGainer.changePct.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="mb-1 text-muted">Top Loser</p>
          <p className="font-medium text-negative">
            {topLoser.symbol} {topLoser.changePct.toFixed(2)}%
          </p>
        </div>
        <div className="col-span-2">
          <p className="mb-1 text-muted">Total Volume (last session, 7 names)</p>
          <p className="font-medium">{totalVolume != null ? totalVolume.toLocaleString() : "not available"}</p>
        </div>
      </div>
    </div>
  );
}
