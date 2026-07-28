"use client";

import { useState } from "react";
import type { ComparisonRow, CompanyOverview, PriceBar, RatioBenchmark, SignalResearch } from "@/lib/api";
import SummaryTab from "./SummaryTab";
import CompanyProfile from "./CompanyProfile";
import OwnershipAndGovernance from "./OwnershipAndGovernance";
import SubsidiaryContribution from "./SubsidiaryContribution";
import ThesisCasesPanel from "./ThesisCasesPanel";
import OperationalKpis from "./OperationalKpis";
import FinancialsChart from "./FinancialsChart";
import RatioGrid from "./RatioGrid";
import TechnicalsTab from "./TechnicalsTab";
import PayoutsAndAnnouncements from "./PayoutsAndAnnouncements";
import CompetitorsTab from "./CompetitorsTab";
import DataQualityPanel from "./DataQualityPanel";
import AISignalTab from "./AISignalTab";
import FinancialStatementsPanel from "./FinancialStatementsPanel";

const TABS = [
  "Summary",
  "Profile",
  "Operations",
  "Financials",
  "Ratios",
  "Technicals",
  "Announcements",
  "Competitors",
  "AI Signal",
] as const;
type Tab = (typeof TABS)[number];

export default function CompanyTabs({
  data,
  comparison,
  benchmarks,
  prices,
  securityId,
  signal,
}: {
  data: CompanyOverview;
  comparison: ComparisonRow[];
  benchmarks: Record<string, RatioBenchmark>;
  prices: PriceBar[];
  securityId: number | null;
  signal: SignalResearch | null;
}) {
  const [active, setActive] = useState<Tab>("Summary");

  return (
    <div>
      <div className="mb-5 flex flex-wrap gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              active === tab
                ? "border-b-2 border-accent text-accent"
                : "text-muted hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {active === "Summary" && <SummaryTab data={data} prices={prices} />}

      {active === "Profile" && (
        <div className="flex flex-col gap-6">
          <CompanyProfile issuer={data.issuer} />
          <OwnershipAndGovernance data={data} />
          <ThesisCasesPanel thesis={data.thesis} />
          <SubsidiaryContribution data={data.subsidiary_contributions} />
          <DataQualityPanel sources={data.sources} />
        </div>
      )}

      {active === "Operations" && <OperationalKpis metrics={data.operational_metrics} />}

      {active === "Financials" && (
        <div>
          <FinancialsChart
            revenue={data.financials["revenue"]}
            profitAfterTax={data.financials["profit_after_tax"]}
            eps={data.financials["eps"]}
          />
          <FinancialStatementsPanel financials={data.financials} />
        </div>
      )}

      {active === "Ratios" && <RatioGrid ratios={data.ratios} benchmarks={benchmarks} />}

      {active === "Technicals" && (
        <TechnicalsTab bars={prices} dataDelayNotice={data.data_delay_notice} securityId={securityId} />
      )}

      {active === "Announcements" && <PayoutsAndAnnouncements data={data} />}

      {active === "Competitors" && <CompetitorsTab rows={comparison} issuerId={data.issuer.id} />}

      {active === "AI Signal" && <AISignalTab signal={signal} prices={prices} data={data} />}
    </div>
  );
}
