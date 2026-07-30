import { AlertTriangle, Building2, Factory, Gauge } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchCementSector, fetchCementLiveQuotes } from "@/lib/api";

const NOT_AVAILABLE_LABELS: Record<string, string> = {
  gdp_contribution_pct: "Estimated contribution to GDP",
  psx_index_weight_pct: "Weight in the PSX / KSE-100 index",
  export_contribution: "Export contribution",
};

export default async function CementSectorPage() {
  const [sector, live] = await Promise.all([fetchCementSector(), fetchCementLiveQuotes()]);
  const isLive = !!live && live.quotes.length > 0;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Cement Sector</h1>
          <p className="mb-6 text-sm text-muted">
            PSX Cement sector — every figure below is aggregated from this pilot&apos;s ingested
            company data, not estimated.
          </p>

          {!sector ? (
            <p className="text-sm text-muted">
              Sector data unavailable — backend unreachable or cement companies not yet seeded.
            </p>
          ) : (
            <div className="flex flex-col gap-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <div className="mb-2 flex items-center gap-2 text-muted">
                    <Building2 size={15} />
                    <p className="text-xs">Companies Covered</p>
                  </div>
                  <p className="text-2xl font-semibold">{sector.company_count}</p>
                </div>
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <div className="mb-2 flex items-center gap-2 text-muted">
                    <Gauge size={15} />
                    <p className="text-xs">Aggregate Market Cap</p>
                  </div>
                  <p className="text-2xl font-semibold">
                    {sector.aggregate_market_cap_pkr != null
                      ? `PKR ${(sector.aggregate_market_cap_pkr / 1_000_000).toFixed(1)} bn`
                      : "—"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {sector.companies_with_market_cap} of {sector.company_count} companies have a
                    reconciled market-cap fact on file
                  </p>
                </div>
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <div className="mb-2 flex items-center gap-2 text-muted">
                    <Factory size={15} />
                    <p className="text-xs">Avg. Capacity Utilization</p>
                  </div>
                  <p className="text-2xl font-semibold">
                    {sector.avg_capacity_utilization_pct != null
                      ? `${sector.avg_capacity_utilization_pct.toFixed(1)}%`
                      : "—"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {sector.companies_with_utilization_data} of {sector.company_count} companies
                    have this KPI on file
                  </p>
                </div>
              </div>

              {/* Live quotes table */}
              {live && live.quotes.length > 0 && (
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <h3 className="mb-3 font-semibold">Live Quotes</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left">
                          <th className="pb-2 pr-6 text-xs font-normal text-muted">Symbol</th>
                          <th className="pb-2 px-4 text-xs font-normal text-muted text-right">Price</th>
                          <th className="pb-2 px-4 text-xs font-normal text-muted text-right">Change</th>
                          <th className="pb-2 px-4 text-xs font-normal text-muted text-right">P/E</th>
                          <th className="pb-2 px-4 text-xs font-normal text-muted text-right">Vol</th>
                        </tr>
                      </thead>
                      <tbody>
                        {live.quotes.map((q) => (
                          <tr key={q.symbol} className="border-b border-border/40">
                            <td className="py-2.5 pr-6 font-medium">{q.symbol}</td>
                            <td className="py-2.5 px-4 text-right tabular-nums">
                              {q.price != null ? `PKR ${q.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "—"}
                            </td>
                            <td className={`py-2.5 px-4 text-right tabular-nums font-medium ${
                              q.change_pct == null ? "text-muted" : q.change_pct >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}>
                              {q.change_pct != null ? `${q.change_pct >= 0 ? "+" : ""}${q.change_pct.toFixed(2)}%` : "—"}
                            </td>
                            <td className="py-2.5 px-4 text-right tabular-nums text-muted">
                              {q.pe_ratio != null ? q.pe_ratio.toFixed(1) : "—"}
                            </td>
                            <td className="py-2.5 px-4 text-right tabular-nums text-muted">
                              {q.volume != null ? (q.volume / 1000).toFixed(0) + "k" : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-2 text-[10px] text-muted">{live.disclaimer}</p>
                </div>
              )}

              <div className="rounded-2xl border border-border bg-surface p-5">
                <h3 className="mb-3 font-semibold">Companies in Coverage</h3>
                <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
                  {sector.companies.map((name) => (
                    <li key={name} className="rounded-lg bg-surface-alt px-3 py-2 text-muted">
                      {name}
                    </li>
                  ))}
                </ul>
              </div>

              {sector.not_available.length > 0 && (
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <div className="mb-2 flex items-center gap-2 text-accent-yellow">
                    <AlertTriangle size={15} />
                    <h3 className="font-semibold">Not Yet Sourced</h3>
                  </div>
                  <p className="mb-2 text-xs text-muted">
                    These fields are part of the sector-card spec but have no ingested data source
                    in this pilot yet, so they are omitted rather than estimated:
                  </p>
                  <ul className="list-inside list-disc text-xs text-muted">
                    {sector.not_available.map((key) => (
                      <li key={key}>{NOT_AVAILABLE_LABELS[key] ?? key}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
