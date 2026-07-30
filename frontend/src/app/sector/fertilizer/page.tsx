import Link from "next/link";
import { AlertTriangle, Building2, ChevronRight, Factory, Gauge } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchFertilizerSector, fetchLiveQuotes } from "@/lib/api";

const NOT_AVAILABLE_LABELS: Record<string, string> = {
  gdp_contribution_pct: "Estimated contribution to GDP",
  psx_index_weight_pct: "Weight in the PSX / KSE-100 index",
  export_contribution: "Export contribution",
};

export default async function FertilizerSectorPage() {
  const [sector, live] = await Promise.all([fetchFertilizerSector(), fetchLiveQuotes()]);
  const isLive = !!live && live.quotes.length > 0;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Fertilizer Sector</h1>
          <p className="mb-6 text-sm text-muted">
            PSX Fertilizer sector classification — every figure below is aggregated from this
            pilot&apos;s own ingested company data, not estimated.
          </p>

          {!sector ? (
            <p className="text-sm text-muted">Sector data unavailable — backend unreachable.</p>
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

              <div className="rounded-2xl border border-border bg-surface p-5">
                <h3 className="mb-3 font-semibold">Companies in Coverage</h3>
                <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                  {sector.companies.map((company) => (
                    <li key={company.id}>
                      <Link
                        href={`/companies/${company.id}`}
                        className="group flex items-center justify-between rounded-lg bg-surface-alt px-3 py-2 text-muted hover:bg-surface hover:text-foreground transition-colors"
                      >
                        <span>
                          {company.symbol && (
                            <span className="mr-2 font-medium text-foreground">{company.symbol}</span>
                          )}
                          {company.name}
                        </span>
                        <ChevronRight size={13} className="shrink-0 text-muted/40 group-hover:text-accent transition-colors" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {sector.total_production_volume != null && (
                <div className="rounded-2xl border border-border bg-surface p-5">
                  <h3 className="mb-1 font-semibold">Total Production Volume</h3>
                  <p className="text-xl font-semibold">{sector.total_production_volume.toLocaleString()}</p>
                  <p className="mt-1 text-[11px] text-muted">
                    Sum of latest total-fertilizer production volume — only{" "}
                    {sector.companies_with_production_data} of {sector.company_count} companies have
                    this figure on file, so this is a partial total, not full-sector production.
                  </p>
                </div>
              )}

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
