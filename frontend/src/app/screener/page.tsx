import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import ScreenerTable from "@/components/screener/ScreenerTable";
import { fetchComparison } from "@/lib/api";

export default async function ScreenerPage() {
  const rows = await fetchComparison();

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Screener</h1>
          <p className="mb-6 text-sm text-muted">
            Filter and rank the {rows.length} currently-listed Fertilizer sector companies by
            price, valuation, and profitability. Every figure is real (live quote or the latest
            reconciled financial_fact/ratio_value on file) — a blank cell means no such record
            exists yet, not zero. AI Signal is locked pending compliance review, not a
            fabricated rating.
          </p>

          {rows.length === 0 ? (
            <p className="text-sm text-muted">Screener data unavailable — backend unreachable.</p>
          ) : (
            <ScreenerTable rows={rows} />
          )}
        </main>
      </div>
    </div>
  );
}
