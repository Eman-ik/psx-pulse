import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import ScreenerTable from "@/components/screener/ScreenerTable";
import { fetchComparison } from "@/lib/api";

export default async function ScreenerPage() {
  const rows = await fetchComparison();
  const liveCount = rows.filter((r) => r.coverage_status === "live").length;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Screener</h1>
          <p className="mb-6 text-sm text-muted">
            {rows.length} listed companies tracked across every PSX sector — {liveCount} with live
            price + financials coverage (🟢 Live), the rest historical-data-only (🟡) or not yet
            populated (🔴). Filter by price, valuation, growth, and profitability below. Every
            figure is real (live quote or the latest reconciled financial_fact/ratio_value on
            file) — a blank cell means no such record exists yet, not zero. AI Signal/Score are
            real research-only scoring output (see the tooltip on each badge), not a fabricated
            rating.
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
