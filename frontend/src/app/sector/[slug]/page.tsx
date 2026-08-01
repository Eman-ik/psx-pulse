import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import CompaniesTable from "@/components/companies/CompaniesTable";
import {
  fetchComparison,
  fetchFertilizerSector,
  fetchCementSector,
  fetchLiveQuotes,
  type ComparisonRow,
} from "@/lib/api";
import { SECTOR_BY_SLUG, COLOR } from "@/lib/sector-config";

interface Props {
  params: Promise<{ slug: string }>;
}

export default async function SectorDetailPage({ params }: Props) {
  const { slug } = await params;
  const sector = SECTOR_BY_SLUG[slug];
  if (!sector) notFound();

  const [allRows, live] = await Promise.all([fetchComparison(), fetchLiveQuotes()]);
  const isLive = live != null && live.quotes.length > 0;

  // Filter comparison rows to this sector's companies
  let rows: ComparisonRow[] = [];

  if (slug === "fertilizer") {
    const data = await fetchFertilizerSector();
    if (data) {
      const ids = new Set(data.companies.map((c) => c.id));
      rows = allRows.filter((r) => ids.has(r.id));
    }
  } else if (slug === "cement") {
    const data = await fetchCementSector();
    if (data) {
      const ids = new Set(data.companies.map((c) => c.id));
      rows = allRows.filter((r) => ids.has(r.id));
    }
  }

  const c = COLOR[sector.color] ?? COLOR.gray;
  const Icon = sector.icon;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          {/* Back */}
          <Link
            href="/sector"
            className="mb-5 inline-flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors"
          >
            <ArrowLeft size={13} />
            All Sectors
          </Link>

          {/* Header */}
          <div className="mb-6 flex items-center gap-4">
            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${c.box} ${c.icon}`}>
              <Icon size={22} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">{sector.name}</h1>
              <p className="text-sm text-muted">{sector.companies} listed companies on PSX</p>
            </div>
          </div>

          {/* Stats strip */}
          <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "GDP Share", value: `${sector.gdpSharePct.toFixed(1)}%` },
              { label: "PSX Weight", value: `${sector.psxWeightPct.toFixed(1)}%` },
              {
                label: "Market Cap (est.)",
                value: `PKR ${sector.marketCapPkrBn >= 100 ? sector.marketCapPkrBn.toFixed(0) : sector.marketCapPkrBn.toFixed(1)} B`,
              },
              { label: "Export Share", value: `${sector.exportSharePct.toFixed(1)}%` },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-2xl border border-border bg-surface p-4">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted/60">{label}</p>
                <p className="text-lg font-bold tabular-nums">{value}</p>
              </div>
            ))}
          </div>

          {/* Description */}
          <div className="mb-6 rounded-2xl border border-border bg-surface p-5">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted/60">Sector Overview</p>
            <p className="text-sm leading-relaxed text-muted">{sector.description}</p>
            <p className="mt-3 text-[11px] text-muted/60">
              <span className="font-semibold text-muted">Specialized Metrics: </span>
              {sector.specializedMetrics}
            </p>
          </div>

          {/* Companies */}
          <h2 className="mb-3 font-semibold">Companies</h2>

          {sector.hasData ? (
            rows.length === 0 ? (
              <p className="text-sm text-muted">Company data unavailable — backend unreachable.</p>
            ) : (
              <>
                <p className="mb-4 text-sm text-muted">
                  {rows.length} companies covered — search, compare, and click through for full
                  research pages.
                </p>
                <CompaniesTable rows={rows} />
              </>
            )
          ) : (
            <div className="rounded-2xl border border-border/50 bg-surface/50 p-8 text-center">
              <p className="mb-1 font-medium text-muted">Full company data not yet available</p>
              <p className="text-sm text-muted/60">
                This sector is in our research pipeline. Price history, financial facts, and AI
                signal coverage will be added in a future release.
              </p>
            </div>
          )}

          {sector.hasData && (
            <p className="mt-4 text-[11px] text-muted/60">
              Price, P/E, and market cap are live or EOD figures sourced from psxdata. ROE and
              dividend yield are the latest reconciled financial_fact/ratio_value on file. AI
              Signal is locked pending compliance review — not a fabricated rating.
            </p>
          )}
        </main>
      </div>
    </div>
  );
}
