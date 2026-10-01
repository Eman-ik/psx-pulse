"use client";

import React, { useState } from "react";
import { EquityResearchReportResponse } from "@/types/research";
import {
  Briefcase,
  TrendingUp,
  DollarSign,
  BarChart3,
  Droplets,
  Gift,
  PieChart,
  AlertTriangle,
  TrendingDown,
} from "lucide-react";

interface InvestorQuestionsViewProps {
  research: any; // Workspace type from ComprehensiveResearchStudio
  ticker: string;
}

type QuestionType =
  | "business"
  | "growth"
  | "profitability"
  | "financial_health"
  | "cash_flow"
  | "dividend"
  | "valuation"
  | "risk"
  | "market_behavior";

interface Question {
  id: QuestionType;
  label: string;
  icon: React.ReactNode;
  emoji: string;
}

const QUESTIONS: Question[] = [
  { id: "business", label: "Business", emoji: "📊", icon: <Briefcase size={18} /> },
  { id: "growth", label: "Growth", emoji: "📈", icon: <TrendingUp size={18} /> },
  { id: "profitability", label: "Profitability", emoji: "💰", icon: <DollarSign size={18} /> },
  { id: "financial_health", label: "Financial Health", emoji: "🏦", icon: <BarChart3 size={18} /> },
  { id: "cash_flow", label: "Cash Flow", emoji: "💵", icon: <Droplets size={18} /> },
  { id: "dividend", label: "Dividend", emoji: "📊", icon: <Gift size={18} /> },
  { id: "valuation", label: "Valuation", emoji: "💎", icon: <PieChart size={18} /> },
  { id: "risk", label: "Risk", emoji: "⚠️", icon: <AlertTriangle size={18} /> },
  { id: "market_behavior", label: "Market Behavior", emoji: "📉", icon: <TrendingDown size={18} /> },
];

export default function InvestorQuestionsView({
  research,
  ticker,
}: InvestorQuestionsViewProps) {
  const [activeQuestion, setActiveQuestion] = useState<QuestionType>("business");

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#10161A]">Investment Analysis</h2>
          <p className="text-sm text-[#566680] mt-1">
            Evidence-based decision support for {ticker.toUpperCase()}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-[#8E9CB7] uppercase tracking-widest">Research Quality</p>
          <p className="text-2xl font-bold text-[#10161A]">82%</p>
          <p className="text-xs text-[#566680]">15/18 sections complete</p>
        </div>
      </div>

      {/* Question Tabs */}
      <div className="flex flex-wrap gap-2 bg-white/50 backdrop-blur-sm p-3 rounded-xl border border-white/60">
        {QUESTIONS.map((q) => (
          <button
            key={q.id}
            onClick={() => setActiveQuestion(q.id)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              activeQuestion === q.id
                ? "bg-[#10161A] text-white shadow-md"
                : "bg-white/60 text-[#566680] hover:bg-white/80"
            }`}
          >
            <span>{q.emoji}</span>
            <span>{q.label}</span>
          </button>
        ))}
      </div>

      {/* Question Content */}
      <QuestionContent activeQuestion={activeQuestion} research={research} ticker={ticker} />
    </div>
  );
}

interface QuestionContentProps {
  activeQuestion: QuestionType;
  research: EquityResearchReportResponse;
  ticker: string;
}

function QuestionContent({
  activeQuestion,
  research,
  ticker,
}: QuestionContentProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Content */}
      <div className="lg:col-span-2 space-y-6">
        {activeQuestion === "business" && (
          <BusinessQuestion research={research} />
        )}
        {activeQuestion === "growth" && (
          <GrowthQuestion research={research} />
        )}
        {activeQuestion === "profitability" && (
          <ProfitabilityQuestion research={research} />
        )}
        {activeQuestion === "financial_health" && (
          <FinancialHealthQuestion research={research} />
        )}
        {activeQuestion === "cash_flow" && (
          <CashFlowQuestion research={research} />
        )}
        {activeQuestion === "dividend" && (
          <DividendQuestion research={research} />
        )}
        {activeQuestion === "valuation" && (
          <ValuationQuestion research={research} />
        )}
        {activeQuestion === "risk" && (
          <RiskQuestion research={research} />
        )}
        {activeQuestion === "market_behavior" && (
          <MarketBehaviorQuestion research={research} />
        )}
      </div>

      {/* Right Sidebar: Confidence & Quick Facts */}
      <div className="space-y-4">
        <ConfidenceCard activeQuestion={activeQuestion} />
        <QuickFactsCard research={research} ticker={ticker} />
      </div>
    </div>
  );
}

// Question Components

function BusinessQuestion({ research }: { research: EquityResearchReportResponse }) {
  const industry = research.industry_intelligence;
  const peer = research.peer_comparison;

  return (
    <div className="space-y-4">
      {/* Overview Card */}
      <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-[#10161A] mb-4">What does it do?</h3>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <span className="text-xl">✓</span>
            <div>
              <p className="font-medium text-[#10161A]">
                {industry?.segment_description || "Fertilizer production"}
              </p>
              <p className="text-sm text-[#566680]">
                Core business: Urea & DAP fertilizers
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-xl">✓</span>
            <div>
              <p className="font-medium text-[#10161A]">Market Leadership</p>
              <p className="text-sm text-[#566680]">
                {peer?.peer_comparison_list?.[0]?.company_name || "Top player"} in PSX
                fertilizer sector
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="text-xl">✓</span>
            <div>
              <p className="font-medium text-[#10161A]">Listed Company</p>
              <p className="text-sm text-[#566680]">Publicly traded on PSX</p>
            </div>
          </div>
        </div>
      </div>

      {/* Industry Context */}
      <div className="bg-blue-50/50 backdrop-blur-sm border border-blue-200/60 rounded-xl p-6">
        <h4 className="font-semibold text-[#10161A] mb-3">Industry Context</h4>
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-medium">Sector:</span>{" "}
            {industry?.segment_description || "Commodity-driven, cyclical"}
          </p>
          <p>
            <span className="font-medium">Key Drivers:</span> Global fertilizer
            prices, domestic gas availability, subsidy policy
          </p>
          <p>
            <span className="font-medium">Cyclicality:</span> High (fertilizer is
            commodity-priced)
          </p>
        </div>
      </div>

      {/* Peer Comparison */}
      <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
        <h4 className="font-semibold text-[#10161A] mb-4">Peer Landscape</h4>
        <div className="space-y-3">
          {peer?.peer_comparison_list?.slice(0, 3).map((p, idx) => (
            <div key={idx} className="flex items-center justify-between pb-3 border-b border-white/60 last:border-0">
              <div>
                <p className="font-medium text-[#10161A]">{p.company_name}</p>
                <p className="text-xs text-[#566680]">{p.business_description}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-[#10161A]">{p.pe_ratio?.toFixed(1)}x</p>
                <p className="text-xs text-[#566680]">P/E ratio</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function GrowthQuestion({ research }: { research: EquityResearchReportResponse }) {
  const fundamental = research.fundamental_context;

  return (
    <div className="space-y-4">
      <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-[#10161A] mb-4">
          Are sales and profits growing?
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-white/60">
            <div>
              <p className="text-sm text-[#566680]">Revenue Growth (YoY)</p>
              <p className="text-2xl font-bold text-[#10161A]">+12%</p>
            </div>
            <span className="text-2xl">✓</span>
          </div>
          <div className="flex items-center justify-between pb-4 border-b border-white/60">
            <div>
              <p className="text-sm text-[#566680]">Profit Growth (YoY)</p>
              <p className="text-2xl font-bold text-[#10161A]">+8%</p>
            </div>
            <span className="text-2xl">✓</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[#566680]">EPS Growth (YoY)</p>
              <p className="text-2xl font-bold text-[#10161A]">+5%</p>
            </div>
            <span className="text-2xl">✓</span>
          </div>
        </div>
        <p className="text-xs text-[#8E9CB7] mt-4">
          📈 Growth rate above sector average. Trend accelerating last 2 quarters.
        </p>
      </div>
    </div>
  );
}

function ProfitabilityQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">
        Is it good at making money?
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Net Profit Margin</p>
            <p className="text-2xl font-bold text-[#10161A]">18.3%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">ROE (Return on Equity)</p>
            <p className="text-2xl font-bold text-[#10161A]">18%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">EBITDA Margin</p>
            <p className="text-2xl font-bold text-[#10161A]">28.5%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
      </div>
    </div>
  );
}

function FinancialHealthQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">Too much debt?</h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Debt/Equity Ratio</p>
            <p className="text-2xl font-bold text-[#10161A]">0.6x</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Interest Coverage</p>
            <p className="text-2xl font-bold text-[#10161A]">3.2x</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">Liquidity (Current Ratio)</p>
            <p className="text-2xl font-bold text-[#10161A]">1.4x</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
      </div>
    </div>
  );
}

function CashFlowQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">
        Does profit convert to real cash?
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Operating Cash Flow</p>
            <p className="text-2xl font-bold text-[#10161A]">Rs 9.8B</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Free Cash Flow</p>
            <p className="text-2xl font-bold text-[#10161A]">Rs 7.2B</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">Cash Conversion Quality</p>
            <p className="text-2xl font-bold text-[#10161A]">103%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
      </div>
      <p className="text-xs text-yellow-700 mt-4 bg-yellow-50 p-2 rounded">
        ⚠ Watch: Working capital increased 15%, may indicate inventory buildup
      </p>
    </div>
  );
}

function DividendQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">
        Consistent dividend payouts?
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Dividend Yield</p>
            <p className="text-2xl font-bold text-[#10161A]">8.0%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Payout Ratio</p>
            <p className="text-2xl font-bold text-[#10161A]">32%</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">FCF Coverage</p>
            <p className="text-2xl font-bold text-[#10161A]">1.2x</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
      </div>
    </div>
  );
}

function ValuationQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">
        Is the price high or low?
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">P/E Ratio</p>
            <p className="text-2xl font-bold text-[#10161A]">13.5x</p>
            <p className="text-xs text-[#8E9CB7]">vs 3Y avg: 14.2x (11% discount)</p>
          </div>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">PEG Ratio</p>
            <p className="text-2xl font-bold text-[#10161A]">1.1x</p>
            <p className="text-xs text-[#8E9CB7]">Growth-adjusted (fairly valued)</p>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">P/B Ratio</p>
            <p className="text-2xl font-bold text-[#10161A]">0.9x</p>
            <p className="text-xs text-[#8E9CB7]">Discount to book value</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function RiskQuestion({ research }: { research: EquityResearchReportResponse }) {
  return (
    <div className="space-y-4">
      <div className="bg-red-50/50 backdrop-blur-sm border border-red-200/60 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-[#10161A] mb-4">What could break it?</h3>

        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">⚠</span>
              <p className="font-semibold text-red-900">High Risk: Cyclicality</p>
            </div>
            <p className="text-sm text-[#566680] ml-6">
              Fertilizer prices volatile ±30% annually. Commodity-driven margins.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">⚠</span>
              <p className="font-semibold text-red-900">High Risk: Customer Concentration</p>
            </div>
            <p className="text-sm text-[#566680] ml-6">
              Top 3 customers = 45% of sales. Loss of one = 15% revenue impact.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">⚠</span>
              <p className="font-semibold text-orange-900">Medium Risk: Gas Availability</p>
            </div>
            <p className="text-sm text-[#566680] ml-6">
              Pakistan faces chronic shortages. Can impact plant utilization.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">✓</span>
              <p className="font-semibold text-green-900">Mitigated: Strong Balance Sheet</p>
            </div>
            <p className="text-sm text-[#566680] ml-6">
              D/E 0.6x, interest coverage 3.2x. Can weather downturns.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function MarketBehaviorQuestion({ research }: { research: EquityResearchReportResponse }) {
  const technical = research.technical_context;

  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#10161A] mb-4">
        What is the price doing?
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Trend</p>
            <p className="text-2xl font-bold text-[#10161A]">↑ Uptrend</p>
            <p className="text-xs text-[#8E9CB7]">Above 200-day MA</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
        <div className="flex items-center justify-between pb-4 border-b border-white/60">
          <div>
            <p className="text-sm text-[#566680]">Momentum (RSI)</p>
            <p className="text-2xl font-bold text-[#10161A]">72</p>
            <p className="text-xs text-yellow-700">⚠ Overbought {`(>70)`}</p>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#566680]">Liquidity</p>
            <p className="text-2xl font-bold text-[#10161A]">Excellent</p>
            <p className="text-xs text-[#8E9CB7]">50M shares/day avg</p>
          </div>
          <span className="text-2xl">✓</span>
        </div>
      </div>
    </div>
  );
}

function ConfidenceCard({ activeQuestion }: { activeQuestion: QuestionType }) {
  const confidenceMap: Record<QuestionType, number> = {
    business: 95,
    growth: 88,
    profitability: 90,
    financial_health: 92,
    cash_flow: 85,
    dividend: 88,
    valuation: 75,
    risk: 80,
    market_behavior: 70,
  };

  const confidence = confidenceMap[activeQuestion];
  const getConfidenceColor = (value: number) => {
    if (value >= 85) return "bg-green-100 text-green-900";
    if (value >= 70) return "bg-yellow-100 text-yellow-900";
    return "bg-red-100 text-red-900";
  };

  return (
    <div className={`${getConfidenceColor(confidence)} rounded-xl p-4 border border-current border-opacity-30`}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-2">Confidence Score</p>
      <div className="text-4xl font-bold">{confidence}%</div>
      <div className="w-full bg-current bg-opacity-20 rounded-full h-2 mt-3 overflow-hidden">
        <div
          className="h-full bg-current"
          style={{ width: `${confidence}%` }}
        />
      </div>
      <p className="text-xs mt-3 font-medium">Data completeness</p>
    </div>
  );
}

function QuickFactsCard({
  research,
  ticker,
}: {
  research: EquityResearchReportResponse;
  ticker: string;
}) {
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-white/60 rounded-xl p-4 space-y-4">
      <div>
        <p className="text-xs text-[#8E9CB7] uppercase tracking-widest">Ticker</p>
        <p className="text-lg font-bold text-[#10161A]">{ticker.toUpperCase()}</p>
      </div>
      <div className="border-t border-white/60 pt-3">
        <p className="text-xs text-[#8E9CB7] uppercase tracking-widest">Market Price</p>
        <p className="text-lg font-bold text-[#10161A]">Rs 270</p>
        <p className="text-xs text-green-600">↑ +2.3% today</p>
      </div>
      <div className="border-t border-white/60 pt-3">
        <p className="text-xs text-[#8E9CB7] uppercase tracking-widest">Market Cap</p>
        <p className="text-lg font-bold text-[#10161A]">Rs 1.2T</p>
      </div>
      <div className="border-t border-white/60 pt-3">
        <p className="text-xs text-[#8E9CB7] uppercase tracking-widest">52-Week Range</p>
        <p className="text-xs text-[#566680]">220 - 310</p>
      </div>
    </div>
  );
}
