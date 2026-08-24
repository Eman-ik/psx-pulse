import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import CompaniesTable from "@/components/companies/CompaniesTable";
import { fetchComparison } from "@/lib/api";

export default async function CompaniesPage() {
  const rows = await fetchComparison();

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">PSX Pilot Companies</h1>
          <p className="mb-6 text-sm text-muted">
            {rows.length} companies covered (fertilizer + cement) — search, compare, and click
            through for full research pages.
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
