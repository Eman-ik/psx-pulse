import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import StatCard from "@/components/dashboard/StatCard";
import SectorChart from "@/components/dashboard/SectorChart";
import MarketCapDonut, { DONUT_COLORS } from "@/components/dashboard/MarketCapDonut";
import RiskPanel from "@/components/dashboard/RiskPanel";
import AnnouncementsTable from "@/components/dashboard/AnnouncementsTable";
import RightPanel from "@/components/dashboard/RightPanel";
import { fetchLiveQuotes } from "@/lib/api";
import {
  announcements,
  pilotCompanies,
  sectorIndexHistory,
  sectorMarketCapChangePct,
  sectorMarketCapPkrBn,
  sectorRisk,
} from "@/lib/mock-data";
import type { CompanySummary } from "@/lib/types";

export default async function DashboardPage() {
  const live = await fetchLiveQuotes();
  const isLive = !!live && live.quotes.length > 0;

  const companies: CompanySummary[] = pilotCompanies.map((company) => {
    const quote = live?.quotes.find((q) => q.symbol === company.symbol);
    if (quote && quote.price != null && quote.change_pct != null) {
      return { ...company, price: quote.price, changePct: quote.change_pct };
    }
    return company;
  });

  const latest = sectorIndexHistory[sectorIndexHistory.length - 1];
  const first = sectorIndexHistory[0];
  const sectorIndexChangePct = ((latest.sectorIndex - first.sectorIndex) / first.sectorIndex) * 100;
  const kseChangePct = ((latest.kse100Index - first.kse100Index) / first.kse100Index) * 100;
  const topGainer = [...companies].sort((a, b) => b.changePct - a.changePct)[0];

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex flex-1 flex-col gap-6 px-6 py-6 lg:flex-row lg:px-8">
          <div className="flex min-w-0 flex-1 flex-col gap-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                label="Fertilizer Sector Index"
                value={latest.sectorIndex.toFixed(1)}
                changePct={sectorIndexChangePct}
              />
              <StatCard label="KSE-100 Index" value={latest.kse100Index.toFixed(1)} changePct={kseChangePct} />
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
                      <span className="h-2 w-2 rounded-full bg-accent" /> Sector Index
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-accent-pink" /> KSE-100
                    </span>
                  </div>
                </div>
                <SectorChart data={sectorIndexHistory} />
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

            <RiskPanel risk={sectorRisk} />

            <AnnouncementsTable rows={announcements} />
          </div>

          <RightPanel
            companies={companies}
            sectorMarketCapPkrBn={sectorMarketCapPkrBn}
            sectorMarketCapChangePct={sectorMarketCapChangePct}
            isLive={isLive}
          />
        </main>

        <footer className="border-t border-border px-6 py-4 text-center text-[11px] text-muted lg:px-8">
          Educational research pilot.{" "}
          {isLive
            ? `Prices are live-ish via ${live!.data_source}; market cap and the sector index chart are still sample data.`
            : "Sample data shown — not a live PSX feed."}{" "}
          Not investment advice. Public launch and AI signal output remain disabled pending PSX
          data licensing and SECP compliance review.
        </footer>
      </div>
    </div>
  );
}
