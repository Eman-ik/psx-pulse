import Link from "next/link";
import { ChevronRight, Lock, BarChart2, Wallet } from "lucide-react";
import type { CompanySummary } from "@/lib/types";
import { DONUT_COLORS } from "./MarketCapDonut";

interface RightPanelProps {
  companies: CompanySummary[];
  sectorMarketCapPkrBn: number;
  sectorMarketCapChangePct: number;
  isLive: boolean;
  companyIdBySymbol?: Record<string, number>;
}

export default function RightPanel({
  companies,
  sectorMarketCapPkrBn,
  sectorMarketCapChangePct,
  isLive,
  companyIdBySymbol = {},
}: RightPanelProps) {
  return (
    <aside className="flex w-full flex-col gap-5 lg:w-80 lg:shrink-0">
      {/* Market status, replaces a user profile card — this is a public, no-login research tool */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-accent/15 text-accent">
            <BarChart2 size={20} />
          </span>
          <div>
            <p className="font-medium">PSX Research Pilot</p>
            <p className="text-xs text-muted">
              {isLive ? "Live prices via psxdata · market cap est." : "EOD sample data · updated daily"}
            </p>
          </div>
        </div>
      </div>

      {/* Sector market cap summary */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-sm text-muted">Sector Market Cap <span className="text-[10px] text-muted/60">(est.)</span></p>
          <button className="flex items-center text-xs text-accent hover:underline">
            View more <ChevronRight size={14} />
          </button>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-white">
            <Wallet size={18} />
          </span>
          <div>
            <p className="text-xl font-semibold">
              PKR {sectorMarketCapPkrBn.toLocaleString()} bn
            </p>
            <p className="text-xs text-positive">+{sectorMarketCapChangePct}% this week</p>
          </div>
        </div>
      </div>

      {/* Company list, replaces the "Assets" list */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm text-muted">Companies</p>
          <Link href="/companies" className="flex items-center text-xs text-accent hover:underline">
            View all <ChevronRight size={14} />
          </Link>
        </div>
        <div className="flex max-h-72 flex-col gap-3 overflow-y-auto pr-1">
          {companies.map((c, i) => {
            const issuerId = companyIdBySymbol[c.symbol];
            const row = (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-xs font-semibold text-white"
                    style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                  >
                    {c.symbol.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-sm font-medium">{c.symbol}</p>
                    <p className="text-xs text-muted">PKR {c.marketCapPkrBn} bn (est.)</p>
                  </div>
                </div>
                <span className={`text-xs font-medium ${c.changePct >= 0 ? "text-positive" : "text-negative"}`}>
                  {c.changePct >= 0 ? "+" : ""}
                  {c.changePct.toFixed(1)}%
                </span>
              </div>
            );
            return issuerId ? (
              <Link key={c.symbol} href={`/companies/${issuerId}`} className="rounded-lg -m-1 p-1 hover:bg-surface-alt">
                {row}
              </Link>
            ) : (
              <div key={c.symbol}>{row}</div>
            );
          })}
        </div>
      </div>

      {/* AI signal teaser — intentionally NOT a paid "upgrade" card: signals are gated by
          PUBLIC_SIGNALS_ENABLED pending the compliance review described in the project's
          non-negotiable gate, not by a subscription tier. */}
      <div className="rounded-2xl border border-accent/30 bg-gradient-to-br from-accent/15 to-accent-pink/10 p-5">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface text-accent">
            <Lock size={18} />
          </span>
          <div>
            <p className="font-semibold leading-tight">AI Research Lab</p>
            <p className="text-[10px] text-accent/80 font-medium uppercase tracking-wider">Engine built · pending compliance</p>
          </div>
        </div>
        <div className="mb-4 grid grid-cols-2 gap-2">
          {["Quality", "Growth", "Valuation", "Financial Health", "Catalyst Risk", "Momentum"].map((dim) => (
            <div key={dim} className="flex items-center gap-1.5 text-[11px] text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-accent/40 shrink-0" />
              {dim}
            </div>
          ))}
        </div>
        <p className="mb-4 text-[11px] text-muted/80 leading-relaxed">
          6-dimension composite scoring for all covered companies. Gated pending PSX data
          licensing and SECP research-regulation review — not a paywall.
        </p>
        <button
          disabled
          className="w-full cursor-not-allowed rounded-xl bg-surface-alt py-2.5 text-sm font-medium text-muted"
        >
          Pending compliance review
        </button>
      </div>
    </aside>
  );
}
