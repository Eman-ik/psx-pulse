import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import NewsFeed from "@/components/news/NewsFeed";
import WorldMonitorTerminal from "@/components/worldmonitor/WorldMonitorTerminal";
import { fetchCompanies, fetchNewsAnnouncements, fetchLiveQuotes } from "@/lib/api";

export default async function NewsPage() {
  const [rows, companies, live] = await Promise.all([
    fetchNewsAnnouncements(),
    fetchCompanies(),
    fetchLiveQuotes(),
  ]);
  const isLive = live != null && live.quotes.length > 0;
  const companyById = Object.fromEntries(companies.map((c) => [c.id, { name: c.name, symbol: c.symbol }]));
  const classified = rows.filter((r) => r.sentiment_score != null).length;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={isLive} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">News &amp; Announcements</h1>
          <p className="mb-6 text-sm text-muted">
            {rows.length} real PSX announcements across the Fertilizer sector pilot. Sentiment is
            a keyword-based classification of the headline only ({classified} of {rows.length}{" "}
            classified so far) — not an AI/LLM signal, and not investment advice.
          </p>

          {rows.length === 0 ? (
            <p className="text-sm text-muted">Announcements unavailable — backend unreachable.</p>
          ) : (
            <NewsFeed rows={rows} companyById={companyById} />
          )}
        </main>

        {/* PSX WorldMonitor AI Agent — macro, geopolitical & market intelligence terminal */}
        <div className="border-t border-border">
          <WorldMonitorTerminal />
        </div>
      </div>
    </div>
  );
}
