import { notFound } from "next/navigation";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import CompanyHeader from "@/components/company/CompanyHeader";
import CompanyTabs from "@/components/company/CompanyTabs";
import { fetchComparison, fetchCompanyOverview, fetchPrices, fetchRatioBenchmarks } from "@/lib/api";

export default async function CompanyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const issuerId = Number(id);
  if (!Number.isFinite(issuerId)) notFound();

  const data = await fetchCompanyOverview(issuerId);
  if (!data) notFound();

  const [comparison, benchmarks, priceData] = await Promise.all([
    fetchComparison(),
    fetchRatioBenchmarks(),
    data.security_id != null
      ? fetchPrices(data.security_id)
      : Promise.resolve({ adjusted: false, delayed_data_notice: "", bars: [] }),
  ]);

  const oneYearAgo = new Date();
  oneYearAgo.setDate(oneYearAgo.getDate() - 365);
  const recentBars = priceData.bars.filter((b) => new Date(b.date) >= oneYearAgo);
  const weekRange = recentBars.length
    ? { low: Math.min(...recentBars.map((b) => b.close)), high: Math.max(...recentBars.map((b) => b.close)) }
    : null;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={!!data.live_quote} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <CompanyHeader data={data} weekRange={weekRange} />

          <CompanyTabs
            data={data}
            comparison={comparison}
            benchmarks={benchmarks}
            prices={priceData.bars}
            securityId={data.security_id}
          />
        </main>

        <footer className="border-t border-border px-6 py-4 text-center text-[11px] text-muted lg:px-8">
          Educational research pilot. Ratios and figures shown are a mix of independently
          calculated values and third-party (Capital Stake) reported figures, labeled
          accordingly. Not investment advice.
        </footer>
      </div>
    </div>
  );
}
