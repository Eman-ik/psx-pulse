import Link from "next/link";
import { ChevronRight } from "lucide-react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchLiveQuotes } from "@/lib/api";
import { SECTORS, COLOR } from "@/lib/sector-config";

function SectorCard({ s }: { s: (typeof SECTORS)[number] }) {
  const c = COLOR[s.color] ?? COLOR.gray;
  const Icon = s.icon;

  const inner = (
    <div
      className={`group relative flex h-full flex-col rounded-2xl border bg-surface p-5 transition-colors ${
        s.hasData
          ? "cursor-pointer border-border hover:border-accent/40 hover:bg-surface-alt"
          : "border-border/50"
      }`}
    >
      {!s.hasData && (
        <span className="absolute right-4 top-4 rounded-full bg-surface-alt px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted">
          Soon
        </span>
      )}

      <div className="mb-3 flex items-start gap-3">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${c.box} ${c.icon}`}>
          <Icon size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold leading-tight">{s.name}</h3>
            {s.hasData && (
              <ChevronRight size={15} className="shrink-0 text-muted transition-colors group-hover:text-accent" />
            )}
          </div>
          <p className="text-[11px] text-muted">{s.companies} listed companies</p>
        </div>
      </div>

      <p className="mb-4 line-clamp-2 text-xs leading-relaxed text-muted">{s.description}</p>

      <div className="mb-4 grid grid-cols-2 gap-x-4 gap-y-3">
        <div>
          <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted/60">GDP Share</p>
          <p className="text-sm font-bold tabular-nums">{s.gdpSharePct.toFixed(1)}%</p>
        </div>
        <div>
          <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted/60">PSX Weight</p>
          <p className="text-sm font-bold tabular-nums">{s.psxWeightPct.toFixed(1)}%</p>
        </div>
        <div>
          <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted/60">Market Cap</p>
          <p className="text-sm font-bold tabular-nums">
            PKR {s.marketCapPkrBn >= 100 ? s.marketCapPkrBn.toFixed(0) : s.marketCapPkrBn.toFixed(1)} B
          </p>
        </div>
        <div>
          <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted/60">Export Share</p>
          <p className="text-sm font-bold tabular-nums">{s.exportSharePct.toFixed(1)}%</p>
        </div>
      </div>

      <div className="mt-auto border-t border-border/50 pt-3">
        <p className="mb-1 text-[9px] font-semibold uppercase tracking-wider text-muted/60">Specialized Metrics</p>
        <p className="text-[11px] leading-relaxed text-muted">{s.specializedMetrics}</p>
      </div>
    </div>
  );

  return (
    <Link href={s.href} className="block h-full">
      <div className={!s.hasData ? "opacity-70" : ""}>{inner}</div>
    </Link>
  );
}

export default async function SectorIntelligencePage() {
  const live = await fetchLiveQuotes();
  const isLive = live != null && live.quotes.length > 0;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Sector Intelligence</h1>
          <p className="mb-6 text-sm text-muted">
            Performance, economics, risks, and sector-specific KPIs across all{" "}
            {SECTORS.length} PSX sectors. Fertilizer and Cement have full data
            coverage; all other sectors are coming soon.
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {SECTORS.map((s) => (
              <SectorCard key={s.slug} s={s} />
            ))}
          </div>

          <p className="mt-6 text-[11px] text-muted/60">
            GDP share, PSX weight, market cap, and export share figures are representative
            estimates based on published PSX sector reports and SBP national accounts — not
            live data. Fertilizer and Cement figures reflect the pilot universe ingested into
            this platform.
          </p>
        </main>
      </div>
    </div>
  );
}
