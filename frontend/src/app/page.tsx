import Link from "next/link";
import { Building2, Layers, SlidersHorizontal, Newspaper, ArrowRight, ShieldCheck, Activity } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import StatCard from "@/components/dashboard/StatCard";
import SectorChart from "@/components/dashboard/SectorChart";
import MarketCapDonut, { DONUT_COLORS } from "@/components/dashboard/MarketCapDonut";
import RiskPanel from "@/components/dashboard/RiskPanel";
import SectorBreadth from "@/components/dashboard/SectorBreadth";
import AnnouncementsTable from "@/components/dashboard/AnnouncementsTable";
import RightPanel from "@/components/dashboard/RightPanel";
import { fetchCompanies, fetchIndexPrices, fetchLiveQuotes, fetchNewsAnnouncements, fetchRiskSnapshot } from "@/lib/api";
import {
  announcements as mockAnnouncements,
  pilotCompanies,
  sectorMarketCapPkrBn,
  sectorRisk as mockSectorRisk,
} from "@/lib/mock-data";
import { sentimentLabel } from "@/lib/sentiment";
import type { AnnouncementRow, CompanySummary, IndexPoint } from "@/lib/types";

const CHART_WINDOW = 250; // ~1 year of trading days

export default async function DashboardPage() {
  const [live, companyList, riskSnapshot, newsAnnouncements, kse100, fertix] = await Promise.all([
    fetchLiveQuotes(),
    fetchCompanies(),
    fetchRiskSnapshot(),
    fetchNewsAnnouncements(),
    fetchIndexPrices("KSE100"),
    fetchIndexPrices("FERTIX"),
  ]);
  const isLive = !!live && live.quotes.length > 0;
  const companyIdBySymbol = Object.fromEntries(
    companyList.filter((c) => c.symbol).map((c) => [c.symbol as string, c.id])
  );
  const companyById = Object.fromEntries(companyList.map((c) => [c.id, c]));

  const companies: CompanySummary[] = pilotCompanies.map((company) => {
    const quote = live?.quotes.find((q) => q.symbol === company.symbol);
    if (quote && quote.price != null && quote.change_pct != null) {
      return { ...company, price: quote.price, changePct: quote.change_pct };
    }
    return company;
  });

  const totalVolume = live
    ? live.quotes.reduce<number | null>((sum, q) => (q.volume != null ? (sum ?? 0) + q.volume : sum), null)
    : null;

  const risk = riskSnapshot ?? mockSectorRisk;
  const isRiskSample = riskSnapshot == null;

  const announcementRows: AnnouncementRow[] =
    newsAnnouncements.length > 0
      ? newsAnnouncements.slice(0, 8).map((a) => {
          const company = a.issuer_id != null ? companyById[a.issuer_id] : undefined;
          return {
            date: a.published_at.slice(0, 10),
            company: company?.name ?? "Unknown company",
            symbol: company?.symbol ?? "—",
            category: a.category,
            title: a.title,
            sentimentLabel: sentimentLabel(a.sentiment_score),
          };
        })
      : mockAnnouncements;
  const isAnnouncementsSample = newsAnnouncements.length === 0;

  const topGainer = [...companies].sort((a, b) => b.changePct - a.changePct)[0];

  const kseBars = kse100?.bars ?? [];
  const isKseLive = kseBars.length >= 2;
  const kseLatestBar = kseBars[kseBars.length - 1];
  const kseChangePct = isKseLive
    ? ((kseLatestBar.close - kseBars[kseBars.length - 2].close) / kseBars[kseBars.length - 2].close) * 100
    : 0;
  const kseLevel = isKseLive ? kseLatestBar.close : null;

  const fertixBars = fertix?.bars ?? [];
  const isFertixReal = fertixBars.length >= 2;
  const fertixLatestBar = isFertixReal ? fertixBars[fertixBars.length - 1] : null;
  const fertixFirstBar = isFertixReal ? fertixBars[0] : null;
  const fertixLevel = fertixLatestBar?.close ?? 1000;
  const sectorIndexChangePct = fertixLatestBar && fertixFirstBar
    ? ((fertixLatestBar.close - fertixFirstBar.close) / fertixFirstBar.close) * 100
    : 0;

  const recentFertix = fertixBars.slice(-CHART_WINDOW);
  const kseByDate = new Map(kseBars.map((b) => [b.date, b.close]));
  const alignedPairs = recentFertix
    .map((fb) => ({ date: fb.date, fertixClose: fb.close, kseClose: kseByDate.get(fb.date) ?? null }))
    .filter((p): p is { date: string; fertixClose: number; kseClose: number } => p.kseClose !== null);

  let chartData: IndexPoint[];
  if (alignedPairs.length >= 2) {
    const baseF = alignedPairs[0].fertixClose;
    const baseK = alignedPairs[0].kseClose;
    chartData = alignedPairs.map((p) => ({
      date: p.date.slice(5),
      sectorIndex: (p.fertixClose / baseF) * 100,
      kse100Index: (p.kseClose / baseK) * 100,
    }));
  } else {
    chartData = recentFertix.map((fb) => ({
      date: fb.date.slice(5),
      sectorIndex: (fb.close / (recentFertix[0]?.close ?? 1000)) * 100,
      kse100Index: 100,
    }));
  }

  return (
    <div className="flex min-h-screen w-full bg-[#DAE1EE]">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex flex-1 flex-col gap-6 px-6 py-6 lg:flex-row lg:px-8">
          <div className="flex min-w-0 flex-1 flex-col gap-6">

            {/* EDITORIAL HERO SECTION */}
            <section className="relative overflow-hidden rounded-3xl border border-white/80 bg-gradient-to-br from-white/80 via-[#DAE1EE]/60 to-[#B4C0D5]/40 p-6 md:p-8 backdrop-blur-xl shadow-xs">
              {/* Abstract Water / Foam / Frosted Glass Caustic Ribbon */}
              <div 
                className="pointer-events-none absolute -right-16 -top-24 h-72 w-96 rounded-full bg-gradient-to-bl from-[#B4C0D5]/50 via-[#8E9CB7]/25 to-transparent blur-3xl"
                aria-hidden="true"
              />
              <div 
                className="pointer-events-none absolute right-24 bottom-0 h-40 w-64 rounded-full bg-gradient-to-t from-white/70 to-transparent blur-2xl"
                aria-hidden="true"
              />

              <div className="relative z-10 max-w-3xl">
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/70 px-3 py-1 shadow-2xs backdrop-blur-md">
                  <ShieldCheck size={13} className="text-[#10161A]" />
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-[#566680]">
                    PSX Quantitative Research · Episode 03
                  </span>
                </div>

                <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[#10161A] leading-tight mb-3">
                  Fertilizer Sector Intelligence &amp; Valuation Architecture.
                </h1>

                <p className="text-sm sm:text-base text-[#566680] leading-relaxed mb-6 max-w-2xl font-normal">
                  Calibrated fundamental extraction, real-time index benchmarking, and compliance-gated multi-agent financial consensus across Pakistan Stock Exchange equities.
                </p>

                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href="/screener"
                    className="inline-flex items-center gap-2 rounded-xl bg-[#10161A] px-4 py-2.5 text-xs font-semibold text-[#DAE1EE] shadow-sm hover:bg-[#1A232A] transition-all"
                  >
                    <span>Launch Sector Screener</span>
                    <ArrowRight size={14} />
                  </Link>

                  <Link
                    href="/ranking"
                    className="inline-flex items-center gap-2 rounded-xl border border-[#566680]/30 bg-white/60 px-4 py-2.5 text-xs font-semibold text-[#10161A] backdrop-blur-md hover:bg-white/90 transition-all shadow-2xs"
                  >
                    <Activity size={14} className="text-[#566680]" />
                    <span>View Quality Rankings</span>
                  </Link>
                </div>
              </div>
            </section>

            {/* KEY METRIC STAT CARDS */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                label={`FERTIX Index${isFertixReal ? " (Live Series)" : " (Verified Sample)"}`}
                value={fertixLevel.toFixed(1)}
                changePct={sectorIndexChangePct}
              />
              <StatCard
                label={`KSE-100 Benchmark${isKseLive ? " (EOD Settle)" : ""}`}
                value={kseLevel != null ? kseLevel.toLocaleString(undefined, { maximumFractionDigits: 1 }) : "—"}
                changePct={kseChangePct}
              />
              <StatCard
                label={`Top Sector Mover — ${topGainer.symbol}`}
                value={topGainer.price.toFixed(1)}
                unit="PKR"
                changePct={topGainer.changePct}
              />
            </div>

            {/* QUICK-ACCESS EDITORIAL WORKFLOW STRIP */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { href: "/companies", icon: Building2, label: "Companies", sub: "Equity coverage" },
                { href: "/sector", icon: Layers, label: "Sectors", sub: "20 PSX industries" },
                { href: "/screener", icon: SlidersHorizontal, label: "Screener", sub: "Multi-factor filter" },
                { href: "/news", icon: Newspaper, label: "Disclosures", sub: "Official regulatory filings" },
              ].map(({ href, icon: Icon, label, sub }) => (
                <Link
                  key={href}
                  href={href}
                  className="glass-light flex items-center gap-3 rounded-2xl px-4 py-3.5 hover:bg-white/90 transition-all"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#10161A] text-[#DAE1EE] shadow-2xs">
                    <Icon size={15} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[#10161A] leading-tight">{label}</p>
                    <p className="text-[11px] text-[#566680] mt-0.5">{sub}</p>
                  </div>
                </Link>
              ))}
            </div>

            {/* ASYMMETRICAL MODULAR SHOWCASE: STATISTICS & ANALYTICS */}
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr_1fr]">
              {/* PRIMARY CHART PANEL */}
              <div className="glass-light rounded-2xl p-6 relative overflow-hidden">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-[#8E9CB7]/20 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-mono font-semibold tracking-wider text-[#566680]">
                      RELATIVE PERFORMANCE DYNAMICS
                    </span>
                    <h3 className="text-base font-bold text-[#10161A] tracking-tight">
                      Sector Equal-Weight (FERTIX) vs. KSE-100
                    </h3>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-medium text-[#566680]">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-[#10161A]" />
                      <span className="text-[#10161A] font-semibold">FERTIX</span>
                      <span className="text-[10px] text-[#8E9CB7]">{isFertixReal ? "(Real)" : "(Sample)"}</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-[#566680]" />
                      <span>KSE-100 Benchmark</span>
                    </span>
                  </div>
                </div>

                <SectorChart data={chartData} />
              </div>

              {/* MARKET CAP COMPOSITION DONUT */}
              <div className="glass-light rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <h3 className="font-bold text-sm text-[#10161A] tracking-tight">Market Weight Distribution</h3>
                    <Link href="/sector" className="text-xs font-semibold text-[#10161A] hover:text-[#566680] transition-colors">
                      Decomposition
                    </Link>
                  </div>
                  <p className="mb-3 text-[11px] text-[#566680]">Fertilizer sector enterprise capitalization</p>
                  
                  <MarketCapDonut companies={companies} />
                </div>

                <div className="mt-4 flex flex-col gap-2 pt-3 border-t border-[#8E9CB7]/20">
                  {companies.map((c, i) => (
                    <div key={c.symbol} className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-2 text-[#566680] font-medium">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                        />
                        <span className="font-mono text-[#10161A]">{c.symbol}</span>
                      </span>
                      <span className="font-medium text-[#566680]">{c.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* SECTOR RISK & BREADTH PANELS */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
              <RiskPanel risk={risk} isSample={isRiskSample} />
              <SectorBreadth companies={companies} totalVolume={totalVolume} />
            </div>

            {/* CORPORATE DISCLOSURES TABLE */}
            <AnnouncementsTable rows={announcementRows} isSample={isAnnouncementsSample} />
          </div>

          {/* ASIDE BAR WITH DARK CONTRAST ANCHOR */}
          <RightPanel
            companies={companies}
            sectorMarketCapPkrBn={sectorMarketCapPkrBn}
            isLive={isLive}
            companyIdBySymbol={companyIdBySymbol}
          />
        </main>

        <footer className="border-t border-[#8E9CB7]/25 bg-[rgba(218,225,238,0.7)] px-6 py-5 text-center text-[11px] text-[#566680] lg:px-8 backdrop-blur-md">
          <p className="max-w-4xl mx-auto leading-relaxed">
            Educational research pilot.{" "}
            {isLive
              ? `Prices are live-ish via ${live!.data_source}.`
              : "Sample company prices shown — not a live PSX feed."}{" "}
            {isFertixReal
              ? `FERTIX is a custom equal-weighted fertilizer index from ${fertix!.bars.length} trading days of EOD data (no PSX sub-index published). `
              : "FERTIX is sample data. "}
            {isKseLive ? "KSE-100 is ingested EOD data via psxdata. " : "KSE-100 is sample data. "}
            Market cap figures are estimates. Not investment advice. Public launch and AI signal output
            pending PSX data licensing and SECP compliance review.
          </p>
          <div className="mt-2 text-[10px] font-mono text-[#8E9CB7]">
            PSX-FERTILIZER STUDIO · KHRONOS FRAMEWORK · COOL BLUE-GRAY THEME SPECIFICATION
          </div>
        </footer>
      </div>
    </div>
  );
}
