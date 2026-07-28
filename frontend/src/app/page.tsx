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
  sectorMarketCapChangePct,
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

  // Chart: align FERTIX and KSE-100 bars by date, rebase both to 100 at the chart window start.
  // Only include dates where both series have a bar (same PSX trading calendar).
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
    // No overlap yet — show each series independently rebased to 100
    chartData = recentFertix.map((fb) => ({
      date: fb.date.slice(5),
      sectorIndex: (fb.close / (recentFertix[0]?.close ?? 1000)) * 100,
      kse100Index: 100,
    }));
  }

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex flex-1 flex-col gap-6 px-6 py-6 lg:flex-row lg:px-8">
          <div className="flex min-w-0 flex-1 flex-col gap-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                label={`FERTIX${isFertixReal ? " (real)" : " (sample)"}`}
                value={fertixLevel.toFixed(1)}
                changePct={sectorIndexChangePct}
              />
              <StatCard
                label={`KSE-100 Index${isKseLive ? " (EOD)" : ""}`}
                value={kseLevel != null ? kseLevel.toLocaleString(undefined, { maximumFractionDigits: 1 }) : "—"}
                changePct={kseChangePct}
              />
              <StatCard
                label={`Top Mover — ${topGainer.symbol}`}
                value={topGainer.price.toFixed(1)}
                unit="PKR"
                changePct={topGainer.changePct}
              />
            </div>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr_1fr]">
              <div className="rounded-2xl border border-border bg-surface p-5">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="font-semibold">Statistics</h3>
                  <div className="flex items-center gap-4 text-xs text-muted">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-accent" /> FERTIX{isFertixReal ? " (real, rebased to 100)" : " (sample)"}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-accent-pink" /> KSE-100{isKseLive ? " (real, rebased to 100)" : " (sample)"}
                    </span>
                  </div>
                </div>
                <SectorChart data={chartData} />
              </div>

              <div className="rounded-2xl border border-border bg-surface p-5">
                <div className="mb-1 flex items-center justify-between">
                  <h3 className="font-semibold">Analytics</h3>
                  <button className="text-xs text-accent hover:underline">View more</button>
                </div>
                <p className="mb-2 text-xs text-muted">Market cap composition</p>
                <MarketCapDonut companies={companies} />
                <div className="mt-3 flex flex-col gap-2">
                  {companies.map((c, i) => (
                    <div key={c.symbol} className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-2 text-muted">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: DONUT_COLORS[i % DONUT_COLORS.length] }}
                        />
                        {c.symbol}
                      </span>
                      <span className="font-medium">{c.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
              <RiskPanel risk={risk} isSample={isRiskSample} />
              <SectorBreadth companies={companies} totalVolume={totalVolume} />
            </div>

            <AnnouncementsTable rows={announcementRows} isSample={isAnnouncementsSample} />
          </div>

          <RightPanel
            companies={companies}
            sectorMarketCapPkrBn={sectorMarketCapPkrBn}
            sectorMarketCapChangePct={sectorMarketCapChangePct}
            isLive={isLive}
            companyIdBySymbol={companyIdBySymbol}
          />
        </main>

        <footer className="border-t border-border px-6 py-4 text-center text-[11px] text-muted lg:px-8">
          Educational research pilot.{" "}
          {isLive
            ? `Prices are live-ish via ${live!.data_source}.`
            : "Sample company prices shown — not a live PSX feed."}{" "}
          {isFertixReal
            ? `FERTIX is a custom equal-weighted price-return index computed from ${fertix!.bars.length} trading days of PriceOHLCV data (no published PSX fertilizer sub-index exists). `
            : "Fertilizer Sector Index is sample data. "}
          {isKseLive
            ? "KSE-100 is ingested EOD data via psxdata. "
            : "KSE-100 figures are still sample data. "}
          Market cap figures remain sample data. Not investment advice. Public launch and AI signal
          output remain disabled pending PSX data licensing and SECP compliance review.
        </footer>
      </div>
    </div>
  );
}
