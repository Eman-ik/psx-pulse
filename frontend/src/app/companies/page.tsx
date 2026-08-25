import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import CompaniesTable from "@/components/companies/CompaniesTable";
import { fetchComparison } from "@/lib/api";

export default async function CompaniesPage() {
  const rows = await fetchComparison();
  const liveCount = rows.filter((r) => r.coverage_status === "live").length;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">PSX Listed Companies</h1>
          <p className="mb-6 text-sm text-muted">
            {rows.length} listed companies tracked — {liveCount} with full live coverage (🟢
            Live: live price + financials), the rest historical-data-only (🟡) or not yet
            populated (🔴). Search, compare, and click through for full research pages.
          </p>

          {rows.length === 0 ? (
            <p className="text-sm text-muted">Company data unavailable — backend unreachable.</p>
          ) : (
            <CompaniesTable rows={rows} />
          )}
        </main>
      </div>
    </div>
  );
}
