import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import ScreenerTable from "@/components/screener/ScreenerTable";
import { fetchComparison, fetchLiveQuotes } from "@/lib/api";

export default async function RankingPage() {
  const [rows, live] = await Promise.all([fetchComparison(), fetchLiveQuotes()]);
  const isLive = live != null && live.quotes.length > 0;
  const scoredCount = rows.filter((r) => r.ai_score != null).length;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">AI Stock Ranking</h1>
          <p className="mb-6 text-sm text-muted">
            Ranks the {scoredCount} of {rows.length} covered companies with a real scoring run on
            file, by AI Score (highest first). This is a rules-based composite over real financial
            and market data — research-only output, not a regulated recommendation (see each
            badge&apos;s tooltip). Still filterable and re-sortable by any column below.
          </p>

          {rows.length === 0 ? (
            <p className="text-sm text-muted">Ranking data unavailable — backend unreachable.</p>
          ) : (
            <ScreenerTable rows={rows} mode="ranking" />
          )}
        </main>
      </div>
    </div>
  );
}
