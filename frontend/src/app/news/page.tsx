import Sidebar from "@/components/dashboard/Sidebar";
import WorldMonitorTerminal from "@/components/worldmonitor/WorldMonitorTerminal";
import { fetchCompanies, fetchNewsAnnouncements, fetchLiveQuotes, fetchComparison } from "@/lib/api";

export default async function NewsPage() {
  const [rows, companies, live, comparison] = await Promise.all([
    fetchNewsAnnouncements(),
    fetchCompanies(),
    fetchLiveQuotes(),
    fetchComparison(),
  ]);

  const companyById = Object.fromEntries(
    companies.map((c) => [c.id, { name: c.name, symbol: c.symbol }])
  );

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <WorldMonitorTerminal
          realAnnouncements={rows}
          companyById={companyById}
          liveQuotes={live?.quotes ?? []}
          comparison={comparison}
        />
      </div>
    </div>
  );
}
