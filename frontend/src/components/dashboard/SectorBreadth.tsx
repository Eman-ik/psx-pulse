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
    ["Advancers", advancers.length, "bg-[#10161A]", ArrowUp],
    ["Decliners", decliners.length, "bg-[#8E9CB7]", ArrowDown],
    ["Unchanged", unchanged.length, "bg-[#B4C0D5]", Minus],
  ];

  return (
    <div className="glass-light rounded-2xl p-5 relative overflow-hidden">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-bold text-[#10161A] tracking-tight">Fertilizer Sector Breadth</h3>
        <span className="text-xs font-medium text-[#566680]">{companies.length} listed entities</span>
      </div>

      <div className="mb-4 flex flex-col gap-3">
        {rows.map(([label, count, color, Icon]) => (
          <div key={label} className="flex items-center gap-3">
            <Icon size={13} className="text-[#566680]" />
            <span className="w-20 text-xs font-semibold text-[#566680]">{label}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-[#B4C0D5]/35">
              <div className={`h-full rounded-full ${color}`} style={{ width: `${(count / total) * 100}%` }} />
            </div>
            <span className="w-6 text-right text-xs font-bold text-[#10161A]">{count}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-[#8E9CB7]/25 pt-4 text-xs">
        <div className="rounded-xl border border-white/60 bg-white/40 p-2.5">
          <p className="mb-0.5 text-[11px] font-semibold text-[#566680] uppercase">Top Gainer</p>
          <p className="font-bold text-[#10161A]">
            {topGainer.symbol} +{topGainer.changePct.toFixed(2)}%
          </p>
        </div>
        <div className="rounded-xl border border-white/60 bg-white/40 p-2.5">
          <p className="mb-0.5 text-[11px] font-semibold text-[#566680] uppercase">Top Decliners</p>
          <p className="font-bold text-[#566680]">
            {topLoser.symbol} {topLoser.changePct.toFixed(2)}%
          </p>
        </div>
        <div className="col-span-2 rounded-xl border border-white/60 bg-[#B4C0D5]/20 p-2.5">
          <p className="mb-0.5 text-[11px] font-semibold text-[#566680] uppercase">Total Trading Volume ({companies.length} names)</p>
          <p className="font-bold text-[#10161A] font-mono text-sm">{totalVolume != null ? totalVolume.toLocaleString() : "not available"}</p>
        </div>
      </div>
    </div>
  );
}
