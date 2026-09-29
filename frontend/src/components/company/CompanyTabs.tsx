"use client";

import { useState } from "react";
import type { ComparisonRow, CompanyOverview, PriceBar, RatioBenchmark } from "@/lib/api";
import { coverageNote, visibleCompanyTabs, type V1CompanyTab } from "@/lib/v1-scope";
import SummaryTab from "./SummaryTab";
import CompanyProfile from "./CompanyProfile";
import OwnershipAndGovernance from "./OwnershipAndGovernance";
import SubsidiaryContribution from "./SubsidiaryContribution";
import ThesisCasesPanel from "./ThesisCasesPanel";
import FinancialsChart from "./FinancialsChart";
import RatioGrid from "./RatioGrid";
import TechnicalsTab from "./TechnicalsTab";
import PayoutsAndAnnouncements from "./PayoutsAndAnnouncements";
import CompetitorsTab from "./CompetitorsTab";
import DataQualityPanel from "./DataQualityPanel";
import FinancialStatementsPanel from "./FinancialStatementsPanel";
import AnalystWorkbenchTab from "./AnalystWorkbenchTab";

// The v1 tab set, narrowed further by how well this particular company is covered.
// Parked tabs and the reasons they are parked live in @/lib/v1-scope. Their components
// (OperationalKpis, CompetitorsTab, AISignalTab, MLModelTab, QuantForecastTab) are still
// in the tree and still work -- they are just not wired into the v1 surface.
type Tab = V1CompanyTab;

export default function CompanyTabs({
  data,
  comparison,
  benchmarks,
  prices,
  securityId,
}: {
  data: CompanyOverview;
  comparison: ComparisonRow[];
  benchmarks: Record<string, RatioBenchmark>;
  prices: PriceBar[];
  securityId: number | null;
}) {
  const [active, setActive] = useState<Tab>("Summary");

  const tabs = visibleCompanyTabs(data.coverage_tier);
  const note = coverageNote(data.coverage_tier);

  // A company can lose its fundamentals-backed tabs (tier changes, or navigation between
  // companies reuses this component), which would otherwise leave `active` pointing at a
  // tab that no longer renders anything -- a blank page with no tab highlighted.
  const current: Tab = tabs.includes(active) ? active : "Summary";

  return (
    <div>
      {note && (
        <p className="mb-4 rounded-lg border border-border bg-bg-subtle px-4 py-3 text-[13px] text-muted">
          {note}
        </p>
      )}

      <div className="mb-5 flex flex-wrap gap-1 border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              current === tab
                ? "border-b-2 border-accent text-accent"
                : "text-muted hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {current === "Summary" && <SummaryTab data={data} prices={prices} />}

      {current === "Profile" && (
        <div className="flex flex-col gap-6">
          <CompanyProfile issuer={data.issuer} />
          <OwnershipAndGovernance data={data} />
          <ThesisCasesPanel thesis={data.thesis} />
          <SubsidiaryContribution data={data.subsidiary_contributions} />
          <DataQualityPanel sources={data.sources} />
        </div>
      )}

      {current === "Financials" && (
        <div>
          <FinancialsChart
            revenue={data.financials["revenue"]}
            profitAfterTax={data.financials["profit_after_tax"]}
            eps={data.financials["eps"]}
          />
          <FinancialStatementsPanel financials={data.financials} />
        </div>
      )}

      {current === "Ratios" && <RatioGrid ratios={data.ratios} benchmarks={benchmarks} />}

      {current === "Technicals" && (
        <TechnicalsTab bars={prices} dataDelayNotice={data.data_delay_notice} securityId={securityId} />
      )}

      {current === "Announcements" && <PayoutsAndAnnouncements data={data} />}

      {current === "Competitors" && <CompetitorsTab rows={comparison} issuerId={data.issuer.id} />}

      {current === "Analyst" && <AnalystWorkbenchTab issuerId={data.issuer.id} />}
    </div>
  );
}
