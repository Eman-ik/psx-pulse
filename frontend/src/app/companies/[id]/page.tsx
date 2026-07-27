import { notFound } from "next/navigation";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import CompanyHeader from "@/components/company/CompanyHeader";
import CompanyProfile from "@/components/company/CompanyProfile";
import OwnershipAndGovernance from "@/components/company/OwnershipAndGovernance";
import FinancialsChart from "@/components/company/FinancialsChart";
import RatioGrid from "@/components/company/RatioGrid";
import PayoutsAndAnnouncements from "@/components/company/PayoutsAndAnnouncements";
import DataQualityPanel from "@/components/company/DataQualityPanel";
import OperationalKpis from "@/components/company/OperationalKpis";
import ThesisPanel from "@/components/company/ThesisPanel";
import SubsidiaryContribution from "@/components/company/SubsidiaryContribution";
import { fetchCompanyOverview } from "@/lib/api";

export default async function CompanyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const issuerId = Number(id);
  if (!Number.isFinite(issuerId)) notFound();

  const data = await fetchCompanyOverview(issuerId);
  if (!data) notFound();

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={!!data.live_quote} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <CompanyHeader data={data} />

          <div className="flex flex-col gap-6">
            <CompanyProfile issuer={data.issuer} />
            <OwnershipAndGovernance data={data} />

            <div className="rounded-2xl border border-border bg-surface p-5">
              <h3 className="mb-4 font-semibold">Financials</h3>
              <FinancialsChart
                revenue={data.financials["revenue"]}
                profitAfterTax={data.financials["profit_after_tax"]}
                eps={data.financials["eps"]}
              />
            </div>

            <div>
              <h3 className="mb-3 font-semibold">Ratios &amp; Diagnostics</h3>
              <RatioGrid ratios={data.ratios} />
            </div>

            <div>
              <h3 className="mb-3 font-semibold">Operations &amp; Production</h3>
              <OperationalKpis metrics={data.operational_metrics} />
            </div>

            <ThesisPanel thesis={data.thesis} />
            <SubsidiaryContribution data={data.subsidiary_contributions} />

            <PayoutsAndAnnouncements data={data} />
            <DataQualityPanel sources={data.sources} />
          </div>
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
