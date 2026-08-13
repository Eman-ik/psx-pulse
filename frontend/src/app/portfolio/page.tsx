import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import PortfolioView from "@/components/portfolio/PortfolioView";
import { fetchComparison } from "@/lib/api";

export default async function PortfolioPage() {
  const rows = await fetchComparison();

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Portfolio</h1>
          <p className="mb-6 max-w-3xl text-sm text-muted">
            Track hypothetical or real holdings against live company data on this platform.
            Holdings are stored only in your browser (never sent anywhere) — this is a personal
            tracking tool, not a brokerage account or trade execution system.
          </p>

          {rows.length === 0 ? (
            <p className="text-sm text-muted">Portfolio data unavailable — backend unreachable.</p>
          ) : (
            <PortfolioView rows={rows} />
          )}
        </main>
      </div>
    </div>
  );
}
