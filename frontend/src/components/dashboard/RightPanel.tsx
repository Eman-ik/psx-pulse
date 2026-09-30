import Link from "next/link";
import { ChevronRight, Lock, BarChart2, Wallet } from "lucide-react";
import type { CompanySummary } from "@/lib/types";
import { DONUT_COLORS } from "./MarketCapDonut";

interface RightPanelProps {
  companies: CompanySummary[];
  sectorMarketCapPkrBn: number;
  isLive: boolean;
  companyIdBySymbol?: Record<string, number>;
}

export default function RightPanel({
  companies,
  sectorMarketCapPkrBn,
  isLive,
  companyIdBySymbol = {},
}: RightPanelProps) {
  return (
    <aside className="flex w-full flex-col gap-5 lg:w-80 lg:shrink-0">
      {/* Market status header card */}
      <div className="glass-light rounded-2xl p-5">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#10161A] text-[#DAE1EE] shadow-sm">
            <BarChart2 size={18} />
          </span>
          <div>
            <p className="font-bold text-sm text-[#10161A]">PSX Research Pilot</p>
            <p className="text-[11px] text-[#566680] mt-0.5">
              {isLive ? "Live prices via psxdata · market cap est." : "EOD verified data · updated daily"}
            </p>
          </div>
        </div>
      </div>

      {/* Sector market cap summary */}
      <div className="glass-light rounded-2xl p-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#566680]">
            Sector Market Cap <span className="text-[10px] text-[#8E9CB7]">(est.)</span>
          </p>
          <Link href="/sector" className="flex items-center text-xs font-medium text-[#10161A] hover:text-[#566680] transition-colors">
            Sector <ChevronRight size={13} />
          </Link>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#B4C0D5]/50 border border-white text-[#10161A]">
            <Wallet size={17} />
          </span>
          <div>
            <p className="text-xl font-bold tracking-tight text-[#10161A]">
              PKR {sectorMarketCapPkrBn.toLocaleString()} bn
            </p>
          </div>
        </div>
      </div>

      {/* Company list */}
      <div className="glass-light rounded-2xl p-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#566680]">Coverage Universe</p>
          <Link href="/companies" className="flex items-center text-xs font-medium text-[#10161A] hover:text-[#566680] transition-colors">
            View all <ChevronRight size={13} />
          </Link>
        </div>
        <div className="flex max-h-72 flex-col gap-2 overflow-y-auto pr-1">
          {companies.map((c, i) => {
            const issuerId = companyIdBySymbol[c.symbol];
            const isPos = c.changePct >= 0;
            const row = (
              <div className="flex items-center justify-between p-2 rounded-xl hover:bg-white/50 transition-colors">
                <div className="flex items-center gap-2.5">
                  <span
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-[11px] font-bold text-white shadow-2xs font-mono"
                    style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                  >
                    {c.symbol.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-xs font-bold text-[#10161A] leading-tight">{c.symbol}</p>
                    <p className="text-[10px] text-[#566680]">PKR {c.marketCapPkrBn} bn</p>
                  </div>
                </div>
                <span className={`text-xs font-semibold tracking-tight ${isPos ? "text-[#10161A]" : "text-[#566680]"}`}>
                  {isPos ? "+" : ""}
                  {c.changePct.toFixed(1)}%
                </span>
              </div>
            );
            return issuerId ? (
              <Link key={c.symbol} href={`/companies/${issuerId}`}>
                {row}
              </Link>
            ) : (
              <div key={c.symbol}>{row}</div>
            );
          })}
        </div>
      </div>

      {/* AI signal teaser in Dark Contrast Panel (#10161A) */}
      <div className="panel-dark rounded-2xl p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-[radial-gradient(circle,rgba(142,156,183,0.18)_0%,transparent_70%)] pointer-events-none" />

        <div className="mb-3 flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-[#DAE1EE] border border-white/15">
            <Lock size={15} />
          </span>
          <div>
            <p className="font-bold text-sm text-[#DAE1EE] leading-tight">AI Research Lab</p>
            <p className="text-[10px] text-[#B4C0D5] font-mono tracking-wider">COMPLIANCE REVIEW ACTIVE</p>
          </div>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-2">
          {["Quality", "Growth", "Valuation", "Financial Health", "Catalyst Risk", "Momentum"].map((dim) => (
            <div key={dim} className="flex items-center gap-1.5 text-[11px] text-[#B4C0D5]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#8E9CB7] shrink-0" />
              {dim}
            </div>
          ))}
        </div>

        <p className="mb-4 text-[11px] text-[#8E9CB7] leading-relaxed">
          6-dimension composite scoring for all covered companies. Gated pending PSX data licensing and SECP research-regulation review.
        </p>

        <button
          disabled
          className="w-full cursor-not-allowed rounded-xl bg-white/10 border border-white/15 py-2.5 text-xs font-semibold text-[#DAE1EE]/70 uppercase tracking-wider"
        >
          SECP Gate Enforced
        </button>
      </div>
    </aside>
  );
}
