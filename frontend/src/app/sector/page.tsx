import Link from "next/link";
import { ChevronRight } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchCementSector, fetchFertilizerSector } from "@/lib/api";

function fmt(n: number | null | undefined, suffix = "") {
  if (n == null) return "—";
  return `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
}

function fmtBn(n: number | null | undefined) {
  if (n == null) return "—";
  return `PKR ${(n / 1_000_000).toFixed(0)} bn`;
}

interface SectorCardProps {
  href: string;
  name: string;
  companyCount: number;
  description: string;
  marketCap: number | null;
  avgUtilization: number | null;
  specializedMetrics: string;
  ready: boolean;
}

function SectorCard({
  href,
  name,
  companyCount,
  description,
  marketCap,
  avgUtilization,
  specializedMetrics,
  ready,
}: SectorCardProps) {
  const inner = (
    <div className={`group relative h-full rounded-2xl border bg-surface p-5 transition-colors ${
      ready
        ? "border-border hover:border-accent/40 hover:bg-surface-alt cursor-pointer"
        : "border-border/50 opacity-60 cursor-not-allowed"
    }`}>
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{name}</h3>
          <p className="text-xs text-muted">{companyCount} {ready ? "covered" : "listed"} companies</p>
        </div>
        {ready && (
          <ChevronRight size={16} className="mt-0.5 shrink-0 text-muted group-hover:text-accent transition-colors" />
        )}
      </div>

      <p className="mb-4 text-xs text-muted leading-relaxed line-clamp-2">{description}</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted/60 mb-0.5">Market Cap</p>
          <p className="font-semibold tabular-nums">{fmtBn(marketCap)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted/60 mb-0.5">Avg Utilization</p>
          <p className="font-semibold tabular-nums">{fmt(avgUtilization, "%")}</p>
        </div>
      </div>

      <div className="mt-4 border-t border-border/50 pt-3">
        <p className="text-[10px] uppercase tracking-wider text-muted/60 mb-1">Specialized Metrics</p>
        <p className="text-xs text-muted">{specializedMetrics}</p>
      </div>
    </div>
  );

  if (!ready) return <div>{inner}</div>;
  return <Link href={href} className="block h-full">{inner}</Link>;
}

export default async function SectorIntelligencePage() {
  const [fertilizer, cement] = await Promise.all([
    fetchFertilizerSector(),
    fetchCementSector(),
  ]);

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Sector Intelligence</h1>
          <p className="mb-6 text-sm text-muted">
            Performance, economics, risks and sector-specific KPIs across the PSX
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <SectorCard
              href="/sector/cement"
              name="Cement"
              companyCount={cement?.company_count ?? 11}
              description="The cement sector serves domestic construction, infrastructure and export markets. Key drivers include housing demand, government PSDP spending, coal and gas input costs, and retention pricing."
              marketCap={cement?.aggregate_market_cap_pkr ?? null}
              avgUtilization={cement?.avg_capacity_utilization_pct ?? null}
              specializedMetrics="Dispatches (local+export), capacity utilization, coal cost, retention price, clinker production"
              ready={!!cement && cement.company_count > 0}
            />

            <SectorCard
              href="/sector/fertilizer"
              name="Fertilizer"
              companyCount={fertilizer?.company_count ?? 5}
              description="The fertilizer sector is critical to Pakistan's agriculture-driven economy, producing urea and DAP. Key drivers include gas feedstock pricing, SBP policy rate, government offtake subsidies and crop-cycle demand."
              marketCap={fertilizer?.aggregate_market_cap_pkr ?? null}
              avgUtilization={fertilizer?.avg_capacity_utilization_pct ?? null}
              specializedMetrics="Capacity (tons/day), production volumes, offtake, gas pricing, market share"
              ready={!!fertilizer && fertilizer.company_count > 0}
            />

            <SectorCard
              href="#"
              name="Commercial Banks"
              companyCount={21}
              description="The banking sector is the largest component of the KSE-100, providing credit to the economy. Key metrics include NIM, ADR, NPL ratio, CAR, and deposit growth."
              marketCap={null}
              avgUtilization={null}
              specializedMetrics="Deposits, advances, NIM, ADR, infection ratio, CAR"
              ready={false}
            />

            <SectorCard
              href="#"
              name="Oil & Gas E&P"
              companyCount={4}
              description="The Oil & Gas Exploration & Production sector involves the exploration, development and production of crude oil and natural gas. Key metrics include production volumes, reserves, and realised prices."
              marketCap={null}
              avgUtilization={null}
              specializedMetrics="Production (boe/day), reserves (2P), wellhead prices, depletion rate"
              ready={false}
            />

            <SectorCard
              href="#"
              name="Oil & Gas Marketing"
              companyCount={5}
              description="The Oil & Gas Marketing sector comprises companies engaged in the marketing and distribution of petroleum products. Key metrics include volumes, gross margin per litre, and receivables from government."
              marketCap={null}
              avgUtilization={null}
              specializedMetrics="Volumes (m litres), gross margin/litre, circular debt receivables"
              ready={false}
            />
          </div>

          <p className="mt-6 text-[11px] text-muted">
            Sectors marked as coming soon are not yet covered by this pilot. Only Cement and
            Fertilizer have ingested price history, financial data, and AI signal coverage.
          </p>
        </main>
      </div>
    </div>
  );
}
