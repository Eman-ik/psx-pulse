"use client";

import React, { useState } from "react";
import {
  Search, Loader2, ChevronRight, AlertCircle, Target, Layers,
  FileSearch, Users, Network, Factory, BarChart3, ShieldAlert,
  Coins, LineChart, Gauge, Scale, GitBranch, Award, Building2,
  ClipboardCheck, CheckCircle2, XCircle, AlertTriangle, TrendingUp,
  BookOpen, Zap,
} from "lucide-react";
import { ResearchReport, type ResearchJSON } from "../research/ResearchReport";

// ═══════════════════════════════════════════════════════════════════════════
// Framework data — sourced from the Complete Company Research and
// Equity-Underwriting Framework specification.
// ═══════════════════════════════════════════════════════════════════════════

const CORE_QUESTIONS = [
  { q: "Is the underlying business genuinely healthy?", tag: "Company quality" },
  { q: "Is management creating or destroying shareholder value?", tag: "Stewardship" },
  { q: "What future performance is already priced into the share?", tag: "Expectations" },
  { q: "Is expected upside sufficiently greater than realistic downside?", tag: "Risk / reward" },
];

const WORKFLOW_STAGES = [
  { n: 1,  stage: "Mandate",                 investigate: "Ticker, exchange, security, currency, time horizon, benchmark and analysis date", output: "Clear research scope" },
  { n: 2,  stage: "Evidence collection",     investigate: "Filings, annual reports, quarterly accounts, transcripts, presentations, exchange notices and market data", output: "Source and evidence register" },
  { n: 3,  stage: "Corporate anatomy",       investigate: "Legal entity, sponsors, shareholders, share count, capital structure and group organization", output: "Corporate identity map" },
  { n: 4,  stage: "Subsidiaries",            investigate: "Subsidiaries, associates, joint ventures, cross-holdings, guarantees and minority interests", output: "Full group relationship map" },
  { n: 5,  stage: "Business model",          investigate: "Products, customers, suppliers, pricing, volumes, capacity, costs and unit economics", output: "Business-driver tree" },
  { n: 6,  stage: "Industry",                investigate: "Market structure, competition, regulation, cyclicality, market share and technological risk", output: "Industry-position assessment" },
  { n: 7,  stage: "Management",              investigate: "CEO, CFO, sponsors, board, auditor, incentives, execution and capital-allocation history", output: "Management credibility score" },
  { n: 8,  stage: "Financial reconstruction",investigate: "Five to ten years of normalized income statement, balance sheet and cash flow", output: "Clean historical model" },
  { n: 9,  stage: "Earnings quality",        investigate: "Revenue recognition, accruals, cash conversion, one-offs and accounting policies", output: "Forensic accounting assessment" },
  { n: 10, stage: "Balance-sheet risk",      investigate: "Debt, leases, liquidity, maturity schedule, FX exposure and refinancing", output: "Survival and solvency assessment" },
  { n: 11, stage: "Capital allocation",      investigate: "Capex, acquisitions, dividends, buybacks, dilution and reinvestment returns", output: "Capital-allocation scorecard" },
  { n: 12, stage: "Operating forecast",      investigate: "Segment drivers, volumes, prices, margins, capex and working capital", output: "Three-statement forecast" },
  { n: 13, stage: "Macro & factor exposure", investigate: "Rates, inflation, GDP, FX, commodities, policy and market beta", output: "CAPM / APT risk analysis" },
  { n: 14, stage: "Market expectations",     investigate: "Consensus estimates, valuation history, ownership, liquidity and positioning", output: "“What is priced in?” analysis" },
  { n: 15, stage: "Valuation",               investigate: "DCF, comparables, SOTP, residual income, NAV or probability-weighted methods", output: "Fair-value range" },
  { n: 16, stage: "Scenarios",               investigate: "Base, bull, bear and severe stress cases", output: "Risk / reward distribution" },
  { n: 17, stage: "Thesis",                  investigate: "Mispricing, evidence, catalysts, falsifiers and downside mechanism", output: "Investable thesis or rejection" },
  { n: 18, stage: "Monitoring",              investigate: "KPI triggers, earnings checkpoints, catalysts and thesis-breaking events", output: "Live thesis tracker" },
];

const EVIDENCE_HIERARCHY = [
  "Company annual and quarterly reports",
  "Standalone and consolidated financial statements",
  "Notes to the accounts",
  "PSX announcements and material-information notices",
  "Corporate briefing-session presentations",
  "Management transcripts, AGM commentary and investor presentations",
  "SECP filings and corporate-governance disclosures",
  "SBP, PBS, Ministry of Finance and sector regulators",
  "Industry associations and competitor filings",
  "Market-data and consensus providers",
  "Reputable news and independent industry research",
  "Explicitly identified assumptions",
];

const CLAIM_LABELS = [
  { label: "Verified fact",             color: "#10b981", desc: "Primary source, reconciled" },
  { label: "Management claim",          color: "#3b82f6", desc: "Stated by company, unverified" },
  { label: "Market/consensus estimate", color: "#8b5cf6", desc: "Third-party projection" },
  { label: "Model-derived conclusion",  color: "#06b6d4", desc: "Output of our own model" },
  { label: "Analyst judgment",          color: "#f59e0b", desc: "Reasoned interpretation" },
  { label: "Assumption",                color: "#f97316", desc: "Explicitly assumed input" },
  { label: "Missing evidence",          color: "#ef4444", desc: "Gap flagged, not filled" },
];

const EVIDENCE_METADATA = [
  "Source ID", "Publication date", "Access date", "Financial period",
  "Page or section", "Standalone or consolidated", "Original unit and currency",
  "Reliability level", "Staleness flag",
];

const OWNERSHIP_CHECKS = [
  "Legal company name and ticker", "Ordinary, preference and other listed securities",
  "Issued, paid-up and fully diluted shares", "Free float", "Sponsor / promoter ownership",
  "Institutional and government ownership", "Treasury shares", "Employee options",
  "Convertible securities", "Warrants and contingent dilution",
  "Recent placements, rights issues and splits", "Insider buying and selling",
  "Share pledges, where disclosed", "Cross-shareholdings", "Ultimate beneficial ownership",
  "Auditor and audit-firm tenure", "Credit rating", "Index membership and benchmark weight",
  "Trading liquidity and ownership concentration",
];

const PROMISE_LEDGER_ROWS = [
  "Revenue target", "Margin target", "Capacity expansion", "Debt reduction", "Project completion",
];

const MGMT_CREDIBILITY = {
  "Track record": [
    "Previous companies and positions", "Performance during their tenure",
    "History of turnarounds, expansions or failures", "Experience through economic downturns",
    "Regulatory, legal or governance controversies", "Frequency of senior-management turnover",
    "Dependence on one individual", "Quality of succession planning",
  ],
  "Incentive alignment": [
    "Management shareholding", "Compensation relative to profits and shareholder returns",
    "Bonus metrics — revenue, EBITDA, EPS, FCF or ROIC", "Related-party compensation",
    "Loans or benefits to executives", "Option issuance and dilution",
    "Whether management benefits even when shareholders lose money",
  ],
  "Capital-allocation record": [
    "Amount invested", "Funding source", "Promised return", "Actual cash generation",
    "Return on invested capital", "Effect on debt", "Effect on earnings per share",
    "Effect on shareholder value",
  ],
};

const GROUP_RED_FLAGS = [
  "Profits reported in subsidiaries but no cash reaching the parent",
  "Parent guaranteeing subsidiary debt",
  "Loss-making subsidiaries repeatedly funded by the listed company",
  "Sales between related entities inflating reported revenue",
  "Assets transferred between group companies at questionable prices",
  "Unexplained intercompany receivables",
  "Double leverage at holding-company and subsidiary levels",
  "Circular ownership",
  "Profitable business sitting outside the listed entity",
  "Minority shareholders absorbing disproportionate risk",
];

const FORENSIC_TESTS = [
  "Revenue growing faster than cash collections",
  "Receivables growing faster than sales",
  "Inventory growing despite weak demand",
  "Increasing contract assets or unbilled revenue",
  "Expenses being capitalized",
  "Changes in depreciation lives",
  "Large unexplained “other income”",
  "Recurring “one-time” gains",
  "Asset revaluations supporting profit or equity",
  "Declining cash taxes despite rising reported profit",
  "Unusual related-party transactions",
  "Supplier financing hidden in working capital",
  "Factoring or receivables financing",
  "Off-balance-sheet commitments",
  "Guarantees for group companies",
  "Auditor qualifications",
  "Emphasis-of-matter paragraphs",
  "Restatements",
  "Frequent auditor or CFO changes",
  "Weak segment disclosure",
  "Large goodwill or intangible balances",
  "Acquisition accounting hiding organic deterioration",
  "Growth from lower tax, FX gains or reduced finance cost",
  "EPS growth from accounting adjustments, not operations",
];

const HEALTH_METRICS = {
  "Growth quality": [
    "Revenue and volume CAGR", "Organic versus acquisition-led growth", "Growth per share",
    "Gross-profit growth", "Customer and product concentration", "Backlog conversion",
    "Growth financed by receivables or inventory",
  ],
  "Profitability": [
    "Gross margin", "EBITDA margin", "EBIT margin", "Net margin",
    "Incremental margin", "Segment margins", "Fixed-cost absorption",
  ],
  "Returns": [
    "ROIC versus cost of capital", "ROE through DuPont decomposition",
    "Return on tangible capital", "Return on new capex", "Asset turnover",
    "Reinvestment rate", "Growth produced per rupee invested",
  ],
  "Cash quality": [
    "CFO to net profit", "CFO to EBITDA", "Free-cash-flow margin", "Cash conversion cycle",
    "Receivable days", "Inventory days", "Payable days", "Maintenance-capex burden",
    "Dividend coverage",
  ],
  "Balance-sheet strength": [
    "Net debt / EBITDA", "Debt / equity", "Interest coverage", "Fixed-charge coverage",
    "Short-term debt versus available liquidity", "Debt maturity concentration",
    "Currency mismatch", "Floating-rate exposure", "Covenant headroom", "Refinancing dependence",
  ],
};

const CAPITAL_BUCKETS = [
  "Maintenance capex", "Organic growth capex", "Acquisitions", "Debt repayment",
  "Dividends", "Share repurchases", "Investments in associates", "Related-party funding", "Idle cash",
];

const CAPITAL_QUESTIONS = [
  "Does the company earn more than its cost of capital?",
  "Can it reinvest at similarly attractive returns?",
  "Is growth funded internally or through repeated debt/equity issuance?",
  "Does management acquire businesses at sensible prices?",
  "Are dividends sustainable?",
  "Are buybacks conducted below intrinsic value?",
  "Has growth improved value per share — or only made the company larger?",
];

const SECTOR_ENGINES = [
  { sector: "Banks",           drivers: "NIM, deposit mix, CASA, asset quality, infection ratio, coverage, cost of risk, capital adequacy", formula: null, color: "#3b82f6" },
  { sector: "Fertilizer",      drivers: "Gas availability and pricing, production, offtake, retention prices, inventory, subsidy receivables", formula: "Production × Offtake × Retention price", color: "#10b981" },
  { sector: "Cement",          drivers: "Dispatches, capacity utilization, retention price, coal/energy cost, freight and expansion capex", formula: "Dispatches × Retention price − coal/energy/freight", color: "#f59e0b" },
  { sector: "E&P",             drivers: "Reserves, production, realized prices, lifting costs, receivables and reserve replacement", formula: "Production × Realized price − lifting cost", color: "#8b5cf6" },
  { sector: "Power",           drivers: "Plant availability, heat rate, capacity payments, tariff adjustments and circular-debt exposure", formula: "Availability × Tariff × Capacity/energy payments", color: "#ec4899" },
  { sector: "Textiles",        drivers: "Export orders, product mix, cotton, energy, FX, working capital and customer concentration", formula: null, color: "#06b6d4" },
  { sector: "Pharmaceuticals", drivers: "Product portfolio, DRAP pricing, approvals, imported inputs and pipeline", formula: null, color: "#14b8a6" },
  { sector: "Technology",      drivers: "Revenue retention, customer concentration, dollar revenue, employee costs, capitalized development", formula: "Customers × Revenue per customer × Retention", color: "#f97316" },
  { sector: "Insurance",       drivers: "Premium growth, combined ratio, claims, reserves, solvency and investment-book risk", formula: null, color: "#a855f7" },
  { sector: "Automobiles",     drivers: "Volumes, localization, FX content, pricing, inventory, financing rates and model cycle", formula: null, color: "#ef4444" },
];

const VALUATION_MATRIX = [
  { type: "Mature operating business", methods: "DCF, P/E, EV/EBITDA" },
  { type: "Conglomerate",              methods: "Sum-of-the-parts" },
  { type: "Bank",                      methods: "P/B, residual income, dividend discount" },
  { type: "Insurance",                 methods: "P/B, embedded value, dividend model" },
  { type: "Cyclical / commodity",      methods: "Mid-cycle earnings, NAV, normalized EV/EBITDA" },
  { type: "Asset-heavy company",       methods: "NAV, replacement cost, DCF" },
  { type: "High-growth company",       methods: "DCF, scenario valuation, reverse DCF" },
  { type: "Binary / event-driven",     methods: "Probability-weighted valuation" },
];

const SCENARIOS = [
  { case: "Bull",   assumption: "Strong demand, pricing and operating leverage", output: "Upside value",        color: "#10b981" },
  { case: "Base",   assumption: "Most probable normalized performance",          output: "Central fair value",  color: "#3b82f6" },
  { case: "Bear",   assumption: "Operational disappointment and multiple pressure", output: "Fundamental downside", color: "#f59e0b" },
  { case: "Stress", assumption: "Liquidity, refinancing or severe-cycle shock",  output: "Survival value",      color: "#ef4444" },
];

const STRESS_TESTS = [
  "PKR depreciation", "Interest-rate increase", "Commodity-price shock", "Volume decline",
  "Margin compression", "Delayed project completion", "Customer loss", "Regulatory tariff change",
  "Working-capital blockage", "Refinancing at higher rates", "Equity dilution", "Dividend suspension",
];

const HEALTH_SCORE = [
  { component: "Business quality and competitive position", weight: 15 },
  { component: "Management and governance",                 weight: 15 },
  { component: "Financial and earnings quality",            weight: 20 },
  { component: "Balance-sheet strength",                    weight: 15 },
  { component: "Capital allocation and ROIC",               weight: 15 },
  { component: "Growth runway",                             weight: 10 },
  { component: "Subsidiary transparency and group risk",    weight: 10 },
];

const ATTRACTIVENESS_SCORE = [
  { component: "Valuation and margin of safety",             weight: 25 },
  { component: "Expectations and variant gap",               weight: 20 },
  { component: "Estimate direction",                         weight: 15 },
  { component: "Catalysts and timing",                       weight: 15 },
  { component: "Downside and scenario skew",                 weight: 15 },
  { component: "Liquidity, positioning and technical setup", weight: 10 },
];

const EVIDENCE_CONFIDENCE = [
  { level: "High",   desc: "Primary, recent and reconciled evidence",                  color: "#10b981" },
  { level: "Medium", desc: "Credible but incomplete or partially indirect",            color: "#f59e0b" },
  { level: "Low",    desc: "Material missing information or assumption-heavy analysis", color: "#ef4444" },
];

const FINAL_POSTURES = [
  { posture: "Research-qualified Buy",                 color: "#10b981" },
  { posture: "Hold",                                   color: "#3b82f6" },
  { posture: "Avoid",                                  color: "#ef4444" },
  { posture: "Watchlist — wait for proof",        color: "#f59e0b" },
  { posture: "Preliminary underwrite — insufficient evidence", color: "#8b5cf6" },
  { posture: "Re-underwrite required",                 color: "#f97316" },
];

const DELIVERABLE_ITEMS = [
  "Executive investment view", "Company-health classification", "Stock-attractiveness assessment",
  "Central market debate", "Three-to-five thesis pillars", "What is currently priced in",
  "Company and value-chain explanation", "Sponsor, CEO and management analysis",
  "Complete subsidiary and associate map", "Ten-year normalized financial analysis",
  "Earnings-quality and forensic review", "Balance-sheet and refinancing assessment",
  "Capital-allocation history", "Industry and peer analysis", "Five-year driver-based forecast",
  "CAPM and APT risk analysis", "DCF, comparable and SOTP valuation",
  "Base, bull, bear and stress cases", "Catalysts and timeline", "Ranked risks",
  "Measurable thesis falsifiers", "Monitoring KPI dashboard",
  "Management questions for the next briefing", "Evidence register, missing sources and confidence level",
];

// ═══════════════════════════════════════════════════════════════════════════
// Section navigation
// ═══════════════════════════════════════════════════════════════════════════

type SectionId =
  | "run" | "overview" | "workflow" | "evidence" | "corporate" | "management"
  | "group" | "business" | "financials" | "forensics" | "capital"
  | "forecast" | "risk" | "expectations" | "valuation" | "scenarios"
  | "thesis" | "scoring" | "sectors" | "deliverable";

const SECTIONS: { id: SectionId; label: string; icon: React.ReactNode }[] = [
  { id: "run",          label: "Run Analysis",       icon: <Zap className="w-3.5 h-3.5" /> },
  { id: "overview",     label: "Overview",           icon: <BookOpen className="w-3.5 h-3.5" /> },
  { id: "workflow",     label: "18-Stage Workflow",  icon: <Layers className="w-3.5 h-3.5" /> },
  { id: "evidence",     label: "Evidence",           icon: <FileSearch className="w-3.5 h-3.5" /> },
  { id: "corporate",    label: "Corporate Identity", icon: <Building2 className="w-3.5 h-3.5" /> },
  { id: "management",   label: "Management",         icon: <Users className="w-3.5 h-3.5" /> },
  { id: "group",        label: "Subsidiaries",       icon: <Network className="w-3.5 h-3.5" /> },
  { id: "business",     label: "Business Model",     icon: <Factory className="w-3.5 h-3.5" /> },
  { id: "financials",   label: "Financial Health",   icon: <BarChart3 className="w-3.5 h-3.5" /> },
  { id: "forensics",    label: "Forensics",          icon: <ShieldAlert className="w-3.5 h-3.5" /> },
  { id: "capital",      label: "Capital Allocation", icon: <Coins className="w-3.5 h-3.5" /> },
  { id: "forecast",     label: "Forecasting",        icon: <LineChart className="w-3.5 h-3.5" /> },
  { id: "risk",         label: "CAPM / APT",         icon: <Gauge className="w-3.5 h-3.5" /> },
  { id: "expectations", label: "What's Priced In",   icon: <Target className="w-3.5 h-3.5" /> },
  { id: "valuation",    label: "Valuation",          icon: <Scale className="w-3.5 h-3.5" /> },
  { id: "scenarios",    label: "Scenarios",          icon: <GitBranch className="w-3.5 h-3.5" /> },
  { id: "thesis",       label: "Thesis & Falsifiers",icon: <Target className="w-3.5 h-3.5" /> },
  { id: "scoring",      label: "Scoring Systems",    icon: <Award className="w-3.5 h-3.5" /> },
  { id: "sectors",      label: "PSX Sector Engines", icon: <Factory className="w-3.5 h-3.5" /> },
  { id: "deliverable",  label: "Final Deliverable",  icon: <ClipboardCheck className="w-3.5 h-3.5" /> },
];

// ═══════════════════════════════════════════════════════════════════════════
// Shared primitives
// ═══════════════════════════════════════════════════════════════════════════

function Panel({ title, subtitle, icon, children }: {
  title: string; subtitle?: string; icon?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <section className="bg-[#18181b] border border-[#27272a] rounded-lg p-5 space-y-3">
      <div className="flex items-start gap-2">
        {icon && <span className="text-[#3b82f6] mt-0.5">{icon}</span>}
        <div>
          <h3 className="text-xs font-bold text-[#fafafa] uppercase tracking-wider">{title}</h3>
          {subtitle && <p className="text-[11px] text-[#71717a] mt-0.5 leading-relaxed">{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function CheckList({ items, columns = 2 }: { items: string[]; columns?: number }) {
  return (
    <ul className={`grid gap-x-4 gap-y-1.5 ${columns === 1 ? "grid-cols-1" : columns === 3 ? "grid-cols-1 md:grid-cols-3" : "grid-cols-1 md:grid-cols-2"}`}>
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-[11px] text-[#a1a1aa] leading-snug">
          <span className="w-1 h-1 rounded-full bg-[#3b82f6] shrink-0 mt-1.5" />
          {item}
        </li>
      ))}
    </ul>
  );
}

function Formula({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-[#09090b] border border-[#27272a] rounded px-3 py-2 text-[11px] text-[#10b981] font-mono overflow-x-auto">
      {children}
    </div>
  );
}

function WeightBar({ weight, color = "#3b82f6" }: { weight: number; color?: string }) {
  return (
    <div className="flex items-center gap-2 shrink-0">
      <div className="w-24 h-1.5 bg-[#27272a] rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${weight * 4}%`, backgroundColor: color }} />
      </div>
      <span className="text-[10px] font-mono font-bold w-7 text-right" style={{ color }}>{weight}</span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Main component
// ═══════════════════════════════════════════════════════════════════════════

const QUICK_TICKERS = ["FFC", "EFERT", "FATIMA", "AGL", "AHCL"];

export function EquityResearchTab() {
  const [section, setSection] = useState<SectionId>("run");

  // Research runner state
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ResearchJSON | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stageIdx, setStageIdx] = useState(0);

  const runResearch = async (t: string) => {
    const sym = t.trim().toUpperCase();
    if (!sym) return;
    setLoading(true); setReport(null); setError(null); setStageIdx(0);

    const timer = setInterval(() => {
      setStageIdx(i => (i < WORKFLOW_STAGES.length - 1 ? i + 1 : i));
    }, 5000);

    try {
      const res = await fetch("/api/research/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: sym }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? `Server error ${res.status}`); return; }
      if (!data.report) { setError("No report returned."); return; }
      setStageIdx(WORKFLOW_STAGES.length);
      setReport(data.report as ResearchJSON);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      clearInterval(timer);
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-0 min-h-0">

      {/* ── Section nav ────────────────────────────────────────────────── */}
      <nav className="w-52 shrink-0 border-r border-[#27272a] p-3 space-y-0.5 overflow-y-auto hidden lg:block">
        <p className="text-[9px] font-bold text-[#52525b] uppercase tracking-wider px-2 pb-2">
          Research Framework
        </p>
        {SECTIONS.map(s => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-[11px] font-medium text-left transition-colors ${
              section === s.id
                ? "bg-[#3b82f6]/15 text-[#3b82f6]"
                : "text-[#71717a] hover:text-[#a1a1aa] hover:bg-[#27272a]"
            }`}
          >
            {s.icon}
            <span className="truncate">{s.label}</span>
          </button>
        ))}
      </nav>

      {/* ── Mobile section selector ───────────────────────────────────── */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        <div className="lg:hidden border-b border-[#27272a] p-3">
          <select
            value={section}
            onChange={e => setSection(e.target.value as SectionId)}
            className="w-full bg-[#18181b] border border-[#27272a] rounded px-3 py-2 text-[11px] text-[#fafafa] focus:outline-none focus:border-[#3b82f6]"
          >
            {SECTIONS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </div>

        <div className="p-5 space-y-4 max-w-4xl">

          {/* ═══ RUN ANALYSIS ═══════════════════════════════════════════ */}
          {section === "run" && (
            <>
              <div className="text-center space-y-2 py-4">
                <span className="inline-block text-[9px] font-bold uppercase tracking-widest text-[#3b82f6] border border-[#3b82f6]/30 rounded px-3 py-1 bg-[#3b82f6]/5">
                  Institutional Initiation of Coverage
                </span>
                <h2 className="text-xl font-bold text-[#fafafa]">Equity Research Engine</h2>
                <p className="text-[11px] text-[#71717a] max-w-lg mx-auto leading-relaxed">
                  Enter a PSX ticker. The engine runs the full 18-stage underwriting
                  workflow and returns a structured initiation report with separate
                  company-health and stock-attractiveness verdicts.
                </p>
              </div>

              <div className="max-w-lg mx-auto space-y-3">
                <form
                  onSubmit={e => { e.preventDefault(); runResearch(ticker); }}
                  className="flex gap-2"
                >
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#52525b]" />
                    <input
                      type="text"
                      value={ticker}
                      onChange={e => setTicker(e.target.value)}
                      disabled={loading}
                      placeholder="Ticker or company name…"
                      className="w-full bg-[#18181b] border border-[#27272a] rounded pl-9 pr-3 py-2.5 text-[12px] text-[#fafafa] placeholder-[#52525b] focus:outline-none focus:border-[#3b82f6] disabled:opacity-50"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !ticker.trim()}
                    className="flex items-center gap-1.5 px-4 py-2.5 bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-40 disabled:cursor-not-allowed rounded text-white text-[12px] font-bold transition-colors"
                  >
                    {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    Underwrite
                  </button>
                </form>

                <div className="flex items-center gap-1.5 justify-center flex-wrap">
                  <span className="text-[9px] text-[#52525b] uppercase tracking-wider">Pilot universe:</span>
                  {QUICK_TICKERS.map(t => (
                    <button
                      key={t}
                      disabled={loading}
                      onClick={() => { setTicker(t); runResearch(t); }}
                      className="px-2 py-0.5 border border-[#27272a] rounded text-[10px] text-[#71717a] hover:text-[#fafafa] hover:border-[#3b82f6]/40 transition-colors disabled:opacity-40"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Live stage tracker */}
              {loading && (
                <div className="max-w-2xl mx-auto bg-[#09090b] border border-[#27272a] rounded-lg p-4 space-y-1">
                  <p className="text-[9px] text-[#52525b] uppercase tracking-wider pb-2">
                    Running institutional workflow · 60–90s via claude-opus-5
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1">
                    {WORKFLOW_STAGES.map((s, i) => {
                      const done = i < stageIdx, active = i === stageIdx;
                      return (
                        <div key={s.n} className={`flex items-center gap-2 text-[10px] ${i > stageIdx ? "opacity-25" : ""}`}>
                          <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0 ${
                            done ? "bg-[#10b981]/20 text-[#10b981]" : active ? "bg-[#3b82f6]/20 text-[#3b82f6]" : "bg-[#27272a] text-[#52525b]"
                          }`}>
                            {done ? "✓" : s.n}
                          </span>
                          <span className={done ? "text-[#52525b] line-through" : active ? "text-[#3b82f6]" : "text-[#52525b]"}>
                            {s.stage}
                          </span>
                          {active && <Loader2 className="w-2.5 h-2.5 animate-spin text-[#3b82f6] ml-auto" />}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {error && !loading && (
                <div className="max-w-2xl mx-auto bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="w-4 h-4 text-[#ef4444] shrink-0 mt-0.5" />
                  <div>
                    <p className="text-[12px] font-bold text-[#ef4444]">Analysis Failed</p>
                    <p className="text-[11px] text-[#a1a1aa] mt-0.5">{error}</p>
                  </div>
                </div>
              )}

              {report && !loading && (
                <div className="pt-4 border-t border-[#27272a]">
                  <ResearchReport r={report} />
                </div>
              )}

              {!report && !loading && !error && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 max-w-2xl mx-auto">
                  {CORE_QUESTIONS.map((c, i) => (
                    <div key={i} className="bg-[#18181b] border border-[#27272a] rounded-lg p-3 space-y-1">
                      <span className="text-[9px] font-bold text-[#3b82f6] uppercase tracking-wider">{c.tag}</span>
                      <p className="text-[11px] text-[#a1a1aa] leading-snug">{c.q}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* ═══ OVERVIEW ═══════════════════════════════════════════════ */}
          {section === "overview" && (
            <>
              <Panel
                title="The objective"
                subtitle="Not merely to decide whether it is a “good company.” Four separate questions are answered."
                icon={<BookOpen className="w-4 h-4" />}
              >
                <div className="space-y-2">
                  {CORE_QUESTIONS.map((c, i) => (
                    <div key={i} className="flex items-start gap-3 bg-[#09090b] border border-[#27272a] rounded p-3">
                      <span className="w-5 h-5 rounded-full bg-[#3b82f6]/15 text-[#3b82f6] text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                      <div>
                        <p className="text-[12px] text-[#fafafa] font-medium">{c.q}</p>
                        <span className="text-[9px] text-[#52525b] uppercase tracking-wider">{c.tag}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="The iron rule">
                <div className="space-y-2 text-[12px] leading-relaxed">
                  <p className="text-[#a1a1aa]">
                    A wonderful company can be a terrible investment at the wrong price.
                    A struggling company can occasionally be a good investment if the price
                    assumes something even worse.
                  </p>
                  <p className="text-[#3b82f6] font-medium">
                    Therefore company quality and stock attractiveness are kept separate
                    throughout the analysis — and scored separately.
                  </p>
                </div>
              </Panel>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Panel title="Company Health Score" icon={<Award className="w-4 h-4" />}>
                  <p className="text-[11px] text-[#71717a]">
                    Seven weighted components totalling 100. Measures whether the underlying
                    business is genuinely healthy — independent of price.
                  </p>
                </Panel>
                <Panel title="Stock Attractiveness Score" icon={<Target className="w-4 h-4" />}>
                  <p className="text-[11px] text-[#71717a]">
                    Six weighted components totalling 100. Measures whether the current price
                    offers asymmetric risk / reward — independent of quality.
                  </p>
                </Panel>
              </div>
            </>
          )}

          {/* ═══ WORKFLOW ═══════════════════════════════════════════════ */}
          {section === "workflow" && (
            <Panel
              title="The complete research workflow"
              subtitle="Eighteen sequential stages. Each stage produces a named output that feeds the next."
              icon={<Layers className="w-4 h-4" />}
            >
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr className="border-b border-[#27272a]">
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px] w-8">#</th>
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">Stage</th>
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">What I investigate</th>
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">Main output</th>
                    </tr>
                  </thead>
                  <tbody>
                    {WORKFLOW_STAGES.map(s => (
                      <tr key={s.n} className="border-b border-[#27272a]/50 hover:bg-[#09090b] transition-colors">
                        <td className="py-2 px-2 text-[#3b82f6] font-mono font-bold">{s.n}</td>
                        <td className="py-2 px-2 text-[#fafafa] font-semibold whitespace-nowrap">{s.stage}</td>
                        <td className="py-2 px-2 text-[#71717a] leading-snug">{s.investigate}</td>
                        <td className="py-2 px-2 text-[#10b981] whitespace-nowrap">{s.output}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}

          {/* ═══ EVIDENCE ═══════════════════════════════════════════════ */}
          {section === "evidence" && (
            <>
              <Panel
                title="Evidence hierarchy — PSX"
                subtitle="A point-in-time source register is built before any opinion is formed. Ranked most to least authoritative."
                icon={<FileSearch className="w-4 h-4" />}
              >
                <ol className="space-y-1">
                  {EVIDENCE_HIERARCHY.map((src, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-[11px]">
                      <span className={`w-5 h-5 rounded flex items-center justify-center text-[9px] font-bold shrink-0 font-mono ${
                        i < 3 ? "bg-[#10b981]/15 text-[#10b981]" :
                        i < 7 ? "bg-[#3b82f6]/15 text-[#3b82f6]" :
                        i < 11 ? "bg-[#f59e0b]/15 text-[#f59e0b]" :
                        "bg-[#ef4444]/15 text-[#ef4444]"
                      }`}>{i + 1}</span>
                      <span className="text-[#a1a1aa]">{src}</span>
                    </li>
                  ))}
                </ol>
              </Panel>

              <Panel title="Required metadata per material figure">
                <CheckList items={EVIDENCE_METADATA} columns={3} />
              </Panel>

              <Panel
                title="Claim labelling"
                subtitle="Every material claim carries one label. This prevents management commentary, forecasts and verified results from being mixed together."
              >
                <div className="space-y-1.5">
                  {CLAIM_LABELS.map(c => (
                    <div key={c.label} className="flex items-center gap-2.5">
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded border w-48 shrink-0"
                        style={{ color: c.color, borderColor: `${c.color}40`, backgroundColor: `${c.color}12` }}
                      >
                        {c.label}
                      </span>
                      <span className="text-[11px] text-[#71717a]">{c.desc}</span>
                    </div>
                  ))}
                </div>
              </Panel>
            </>
          )}

          {/* ═══ CORPORATE ══════════════════════════════════════════════ */}
          {section === "corporate" && (
            <>
              <Panel
                title="Corporate identity and ownership"
                subtitle="The first analytical task is establishing exactly what shareholders own."
                icon={<Building2 className="w-4 h-4" />}
              >
                <CheckList items={OWNERSHIP_CHECKS} />
              </Panel>

              <div className="bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-lg p-4 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-[#f59e0b] shrink-0 mt-0.5" />
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  <span className="text-[#f59e0b] font-bold">A concentrated sponsor holding is not automatically good.</span>{" "}
                  Determine whether the sponsor behaves like an aligned long-term owner — or uses
                  the listed company to benefit other group entities.
                </p>
              </div>
            </>
          )}

          {/* ═══ MANAGEMENT ═════════════════════════════════════════════ */}
          {section === "management" && (
            <>
              <Panel
                title="The decision-making stack"
                subtitle="Investigate the complete stack — not just the CEO’s biography."
                icon={<Users className="w-4 h-4" />}
              >
                <div className="flex flex-wrap gap-1.5">
                  {["Sponsors / controlling family", "Chairperson", "CEO", "CFO", "COO",
                    "Segment & subsidiary heads", "Board of directors", "Independent directors",
                    "Audit committee", "Remuneration committee", "Company secretary",
                    "External auditor", "Key related-party entities"].map(r => (
                    <span key={r} className="text-[10px] px-2 py-1 bg-[#09090b] border border-[#27272a] rounded text-[#a1a1aa]">{r}</span>
                  ))}
                </div>
              </Panel>

              <Panel
                title="Management promise ledger"
                subtitle="Reveals whether management consistently underpromises and overdelivers — or repeatedly changes the story."
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#27272a]">
                        {["Statement", "Date promised", "Target period", "Actual outcome", "Variance", "Explanation"].map(h => (
                          <th key={h} className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {PROMISE_LEDGER_ROWS.map(r => (
                        <tr key={r} className="border-b border-[#27272a]/50">
                          <td className="py-2 px-2 text-[#fafafa] font-medium whitespace-nowrap">{r}</td>
                          {Array.from({ length: 5 }).map((_, i) => (
                            <td key={i} className="py-2 px-2 text-[#3f3f46]">—</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              {Object.entries(MGMT_CREDIBILITY).map(([title, items]) => (
                <Panel key={title} title={title}>
                  <CheckList items={items} />
                </Panel>
              ))}

              <div className="bg-[#3b82f6]/5 border border-[#3b82f6]/20 rounded-lg p-4">
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  <span className="text-[#3b82f6] font-bold">The most important management test is not charisma.</span>{" "}
                  It is how intelligently and honestly management has allocated shareholders’ money.
                </p>
              </div>
            </>
          )}

          {/* ═══ GROUP / SUBSIDIARIES ═══════════════════════════════════ */}
          {section === "group" && (
            <>
              <Panel
                title="Subsidiary and associate master schedule"
                subtitle="Subsidiaries are often where hidden value — or hidden risk — sits."
                icon={<Network className="w-4 h-4" />}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#27272a]">
                        {["Entity", "Ownership", "Treatment", "Revenue", "Profit", "Assets", "Debt", "FCF", "Guarantees", "Est. value"].map(h => (
                          <th key={h} className="text-left py-2 px-1.5 text-[#52525b] font-bold uppercase tracking-wider text-[9px] whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { e: "Subsidiary A", t: "Consolidated" },
                        { e: "Associate B",  t: "Equity method" },
                        { e: "JV C",         t: "Equity method" },
                      ].map(row => (
                        <tr key={row.e} className="border-b border-[#27272a]/50">
                          <td className="py-2 px-1.5 text-[#fafafa] font-medium whitespace-nowrap">{row.e}</td>
                          <td className="py-2 px-1.5 text-[#3f3f46]">—</td>
                          <td className="py-2 px-1.5 text-[#71717a] whitespace-nowrap">{row.t}</td>
                          {Array.from({ length: 7 }).map((_, i) => (
                            <td key={i} className="py-2 px-1.5 text-[#3f3f46]">—</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <Panel
                title="Group-level red flags"
                subtitle="Any one of these materially lowers evidence confidence and may block a positive thesis."
                icon={<AlertTriangle className="w-4 h-4" />}
              >
                <ul className="space-y-1.5">
                  {GROUP_RED_FLAGS.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#a1a1aa] leading-snug">
                      <XCircle className="w-3.5 h-3.5 text-[#ef4444] shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>
              </Panel>

              <div className="bg-[#3b82f6]/5 border border-[#3b82f6]/20 rounded-lg p-4">
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  This analysis leads to a proper <span className="text-[#3b82f6] font-bold">sum-of-the-parts valuation</span>{" "}
                  and an assessment of any justified holding-company discount.
                </p>
              </div>
            </>
          )}

          {/* ═══ BUSINESS MODEL ═════════════════════════════════════════ */}
          {section === "business" && (
            <>
              <Panel title="Revenue engine" icon={<Factory className="w-4 h-4" />}>
                <Formula>Revenue = Volume × Realized Price</Formula>
                <CheckList items={[
                  "Products and services", "Revenue by segment, product and geography",
                  "Customer categories", "Recurring versus transactional revenue",
                  "Regulated versus market-based pricing", "Volume growth", "Price growth",
                  "Currency effects", "Acquisitions and disposals", "Customer concentration",
                  "Contract length", "Backlog or order book", "Refunds, discounts and incentives",
                  "Seasonality", "Revenue-recognition policy",
                ]} />
              </Panel>

              <Panel title="Cost engine">
                <CheckList items={[
                  "Raw materials", "Energy", "Labour", "Freight", "Distribution",
                  "Imported inputs", "Royalties", "Maintenance", "Selling costs",
                  "Regulatory costs", "Fixed versus variable costs", "Operating leverage",
                  "Cost pass-through ability",
                ]} columns={3} />
              </Panel>

              <Panel
                title="Competitive advantage"
                subtitle="Every claimed advantage must eventually appear in numbers — superior margins, pricing, retention, market share, cash conversion or ROIC."
              >
                <CheckList items={[
                  "Cost advantage", "Brand power", "Distribution strength", "Switching costs",
                  "Network effects", "Licences or regulatory protection", "Scarce assets",
                  "Economies of scale", "Superior technology",
                  "Exclusive supply or customer relationships",
                  "Structural access to cheaper capital or inputs",
                ]} />
              </Panel>
            </>
          )}

          {/* ═══ FINANCIAL HEALTH ═══════════════════════════════════════ */}
          {section === "financials" && (
            <>
              <Panel
                title="Ten-year financial reconstruction"
                subtitle="Rebuild — not simply copy — the financial statements. Reconcile profits to cash and changes in net debt."
                icon={<BarChart3 className="w-4 h-4" />}
              >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { t: "Income statement", items: ["Revenue by segment", "Gross profit", "Operating expenses", "EBITDA", "D&A", "EBIT", "Finance cost", "Associate income", "Other income", "Tax", "Minority interest", "Reported & normalized earnings", "Basic and diluted EPS"] },
                    { t: "Balance sheet",    items: ["Cash", "Receivables", "Inventory", "Investments", "PP&E", "Intangibles and goodwill", "Payables", "Short- & long-term debt", "Lease liabilities", "Pension obligations", "Deferred tax", "Provisions", "Minority interests", "Shareholders’ equity"] },
                    { t: "Cash flow",        items: ["Cash from operations", "Working-capital movement", "Maintenance capex", "Growth capex", "Acquisitions", "Asset sales", "Interest", "Dividends", "Debt issuance/repayment", "Equity issuance", "Free cash flow"] },
                  ].map(col => (
                    <div key={col.t} className="space-y-1.5">
                      <p className="text-[10px] font-bold text-[#3b82f6] uppercase tracking-wider">{col.t}</p>
                      {col.items.map(i => (
                        <p key={i} className="text-[10px] text-[#71717a] leading-snug">{i}</p>
                      ))}
                    </div>
                  ))}
                </div>
              </Panel>

              <div className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-4 flex items-start gap-3">
                <ShieldAlert className="w-4 h-4 text-[#ef4444] shrink-0 mt-0.5" />
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  <span className="text-[#ef4444] font-bold">Reconciliation gate:</span>{" "}
                  If the financial statements cannot be reconciled, the analysis is not ready for valuation. Stop.
                </p>
              </div>

              <Panel title="Return formulas">
                <div className="space-y-2">
                  <Formula>ROIC = NOPAT / Average Invested Capital</Formula>
                  <Formula>Incremental ROIC = ΔNOPAT / ΔInvested Capital</Formula>
                </div>
              </Panel>

              {Object.entries(HEALTH_METRICS).map(([title, items]) => (
                <Panel key={title} title={title}>
                  <CheckList items={items} />
                </Panel>
              ))}
            </>
          )}

          {/* ═══ FORENSICS ══════════════════════════════════════════════ */}
          {section === "forensics" && (
            <>
              <Panel
                title="Forensic accounting and earnings quality"
                subtitle="This is where apparently healthy companies often begin to break."
                icon={<ShieldAlert className="w-4 h-4" />}
              >
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1.5">
                  {FORENSIC_TESTS.map((t, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#a1a1aa] leading-snug">
                      <span className="w-4 h-4 rounded bg-[#ef4444]/10 text-[#ef4444] text-[8px] font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      {t}
                    </li>
                  ))}
                </ul>
              </Panel>

              <Panel title="Statistical tripwires">
                <div className="flex flex-wrap gap-2 mb-2">
                  {["Piotroski F-score", "Beneish M-score", "Altman Z-score", "Accrual ratios"].map(m => (
                    <span key={m} className="text-[10px] px-2.5 py-1 bg-[#09090b] border border-[#27272a] rounded text-[#a1a1aa] font-mono">{m}</span>
                  ))}
                </div>
                <p className="text-[11px] text-[#f59e0b] leading-relaxed">
                  Used as warning systems — never as standalone investment decisions.
                </p>
              </Panel>
            </>
          )}

          {/* ═══ CAPITAL ALLOCATION ═════════════════════════════════════ */}
          {section === "capital" && (
            <>
              <Panel
                title="Classify every rupee of cash"
                icon={<Coins className="w-4 h-4" />}
              >
                <div className="flex flex-wrap gap-1.5">
                  {CAPITAL_BUCKETS.map(b => (
                    <span key={b} className="text-[10px] px-2.5 py-1 bg-[#09090b] border border-[#27272a] rounded text-[#a1a1aa]">{b}</span>
                  ))}
                </div>
              </Panel>

              <Panel title="The central questions">
                <ul className="space-y-2">
                  {CAPITAL_QUESTIONS.map((q, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-[11px] text-[#a1a1aa] leading-snug">
                      <span className="w-5 h-5 rounded-full bg-[#3b82f6]/15 text-[#3b82f6] text-[9px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </Panel>

              <div className="bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-lg p-4 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-[#f59e0b] shrink-0 mt-0.5" />
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  For capital-intensive companies, no positive thesis is approved until the model
                  includes <span className="text-[#f59e0b] font-bold">maintenance capex, debt, leases,
                  refinancing, dilution and after-financing returns.</span>
                </p>
              </div>
            </>
          )}

          {/* ═══ FORECASTING ════════════════════════════════════════════ */}
          {section === "forecast" && (
            <>
              <Panel
                title="Driver-based three-statement model"
                subtitle="Normally five historical and five forecast years. Built from operational drivers — never arbitrary percentage growth."
                icon={<LineChart className="w-4 h-4" />}
              >
                <Formula>
                  <div className="space-y-0.5 whitespace-pre">
                    {"Operating drivers → Revenue → Margins → Profit"}
                    {"\n                  → Working capital → Cash flow"}
                    {"\n                  → Capex/debt → Balance sheet"}
                    {"\n                  → Interest/tax/share count → EPS and FCF"}
                  </div>
                </Formula>
              </Panel>

              <Panel title="Sector driver formulas">
                <div className="space-y-1.5">
                  {SECTOR_ENGINES.filter(s => s.formula).map(s => (
                    <div key={s.sector} className="flex items-center gap-3">
                      <span className="text-[10px] font-bold w-24 shrink-0" style={{ color: s.color }}>{s.sector}</span>
                      <code className="text-[10px] text-[#a1a1aa] font-mono">{s.formula}</code>
                    </div>
                  ))}
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold w-24 shrink-0 text-[#3b82f6]">Bank</span>
                    <code className="text-[10px] text-[#a1a1aa] font-mono">Deposits × Asset deployment × Spreads − credit costs</code>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold w-24 shrink-0 text-[#f97316]">Retail</span>
                    <code className="text-[10px] text-[#a1a1aa] font-mono">Stores × Sales per store × Margin</code>
                  </div>
                </div>
              </Panel>

              <div className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-4">
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  <span className="text-[#ef4444] font-bold">No forecast is finalized</span> without
                  checking whether cash, debt and equity reconcile.
                </p>
              </div>
            </>
          )}

          {/* ═══ CAPM / APT ═════════════════════════════════════════════ */}
          {section === "risk" && (
            <>
              <Panel
                title="CAPM — cost of equity"
                subtitle="Primarily useful for estimating the discount rate."
                icon={<Gauge className="w-4 h-4" />}
              >
                <Formula>Ke = Rf + β × (Rm − Rf)</Formula>
              </Panel>

              <Panel
                title="APT — which risks actually drive the company"
              >
                <Formula>E(R) = Rf + β₁λ₁ + β₂λ₂ + ⋯ + βₙλₙ</Formula>
                <p className="text-[10px] font-bold text-[#52525b] uppercase tracking-wider pt-2">Potential PSX factors</p>
                <div className="flex flex-wrap gap-1.5">
                  {["Market return", "Interest rates", "Inflation", "PKR/USD",
                    "GDP or industrial production", "Oil, gas, coal or agri commodities",
                    "Sovereign-risk conditions", "Sector index", "Domestic liquidity",
                    "Export demand"].map(f => (
                    <span key={f} className="text-[10px] px-2 py-1 bg-[#09090b] border border-[#27272a] rounded text-[#a1a1aa]">{f}</span>
                  ))}
                </div>
              </Panel>

              <div className="bg-[#3b82f6]/5 border border-[#3b82f6]/20 rounded-lg p-4 space-y-1.5">
                <p className="text-[11px] text-[#a1a1aa]">
                  <span className="text-[#3b82f6] font-bold">CAPM</span> supports the discount rate.
                </p>
                <p className="text-[11px] text-[#a1a1aa]">
                  <span className="text-[#3b82f6] font-bold">APT</span> explains risk drivers and scenario sensitivity.
                </p>
                <p className="text-[11px] text-[#f59e0b] pt-1">
                  Neither replaces fundamental cash-flow analysis. Estimate rolling factor
                  sensitivities, test different economic regimes, and distinguish correlation
                  from actual economic exposure.
                </p>
              </div>
            </>
          )}

          {/* ═══ EXPECTATIONS ═══════════════════════════════════════════ */}
          {section === "expectations" && (
            <>
              <Panel
                title="Market expectations and stock setup"
                subtitle="After understanding the company, investigate the stock."
                icon={<Target className="w-4 h-4" />}
              >
                <CheckList items={[
                  "Current price with timestamp", "Market capitalization", "Enterprise value",
                  "Free float", "Average trading value", "Bid-ask spread", "Historical volatility",
                  "Beta", "Maximum drawdown", "Index membership", "Institutional ownership",
                  "Sponsor transactions", "Valuation history", "Peer valuation",
                  "Consensus estimates", "Estimate revisions", "Price and volume behaviour",
                  "Technical support / resistance", "Event-related gaps",
                ]} />
                <p className="text-[11px] text-[#f59e0b] pt-2 leading-relaxed">
                  Technical analysis is useful for entry timing, liquidity and risk management.
                  It does not determine whether the underlying business is healthy.
                </p>
              </Panel>

              <Panel
                title="Reverse valuation"
                subtitle="Instead of asking only “What is the company worth?”"
              >
                <div className="bg-[#09090b] border border-[#3b82f6]/30 rounded p-3 mb-3">
                  <p className="text-[12px] text-[#3b82f6] font-medium leading-relaxed">
                    What revenue growth, margin, ROIC or cash flow must the company deliver
                    to justify today’s price?
                  </p>
                </div>
                <p className="text-[10px] font-bold text-[#52525b] uppercase tracking-wider pb-1.5">
                  This reveals whether the price assumes
                </p>
                <div className="space-y-1">
                  {[
                    { label: "Decline", color: "#ef4444" },
                    { label: "Normal performance", color: "#71717a" },
                    { label: "A successful turnaround", color: "#3b82f6" },
                    { label: "Permanent high growth", color: "#f59e0b" },
                    { label: "Unrealistic margins", color: "#f97316" },
                    { label: "A flawless expansion project", color: "#ef4444" },
                  ].map(x => (
                    <div key={x.label} className="flex items-center gap-2 text-[11px]">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: x.color }} />
                      <span className="text-[#a1a1aa]">{x.label}</span>
                    </div>
                  ))}
                </div>
              </Panel>
            </>
          )}

          {/* ═══ VALUATION ══════════════════════════════════════════════ */}
          {section === "valuation" && (
            <>
              <Panel
                title="Valuation method by company type"
                subtitle="At least two independent methods are used for every name."
                icon={<Scale className="w-4 h-4" />}
              >
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr className="border-b border-[#27272a]">
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">Company type</th>
                      <th className="text-left py-2 px-2 text-[#52525b] font-bold uppercase tracking-wider text-[9px]">Primary methods</th>
                    </tr>
                  </thead>
                  <tbody>
                    {VALUATION_MATRIX.map(v => (
                      <tr key={v.type} className="border-b border-[#27272a]/50 hover:bg-[#09090b]">
                        <td className="py-2 px-2 text-[#fafafa] font-medium">{v.type}</td>
                        <td className="py-2 px-2 text-[#a1a1aa]">{v.methods}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>

              <Panel title="Enterprise-value bridge">
                <Formula>EV = Equity Value + Debt + Leases + Preference Shares + Minority Interest − Cash</Formula>
              </Panel>

              <Panel title="Equity-value bridge — must account for">
                <CheckList items={[
                  "Net debt", "Lease liabilities", "Minority interests", "Pension deficits",
                  "Preference shares", "Associates and investments", "Non-operating assets",
                  "Contingent dilution", "Fully diluted share count",
                ]} columns={3} />
              </Panel>

              <Panel title="Expected total return">
                <Formula>
                  Expected Total Return = (Target Price − Current Price + Expected Dividends) / Current Price
                </Formula>
                <p className="text-[11px] text-[#f59e0b] pt-2">
                  The final result is a valuation <span className="font-bold">range</span> —
                  never a falsely precise single number.
                </p>
              </Panel>
            </>
          )}

          {/* ═══ SCENARIOS ══════════════════════════════════════════════ */}
          {section === "scenarios" && (
            <>
              <Panel
                title="Four scenarios, internally consistent"
                icon={<GitBranch className="w-4 h-4" />}
              >
                <div className="space-y-2">
                  {SCENARIOS.map(s => (
                    <div key={s.case} className="flex items-start gap-3 bg-[#09090b] border border-[#27272a] rounded p-3">
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded shrink-0 w-16 text-center"
                        style={{ color: s.color, backgroundColor: `${s.color}15` }}
                      >
                        {s.case}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-[#fafafa]">{s.assumption}</p>
                        <p className="text-[10px] text-[#71717a] mt-0.5">→ {s.output}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>

              <div className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded-lg p-4 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-[#ef4444] shrink-0 mt-0.5" />
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  <span className="text-[#ef4444] font-bold">The bear case is not a slightly weaker
                  version of the base case.</span> It must explain exactly how shareholders lose money.
                </p>
              </div>

              <Panel title="Stress tests">
                <div className="flex flex-wrap gap-1.5">
                  {STRESS_TESTS.map(t => (
                    <span key={t} className="text-[10px] px-2 py-1 bg-[#ef4444]/5 border border-[#ef4444]/20 rounded text-[#a1a1aa]">{t}</span>
                  ))}
                </div>
              </Panel>
            </>
          )}

          {/* ═══ THESIS ═════════════════════════════════════════════════ */}
          {section === "thesis" && (
            <>
              <Panel
                title="A strong thesis must state"
                icon={<Target className="w-4 h-4" />}
              >
                <ol className="space-y-2">
                  {[
                    "What the market appears to believe",
                    "What I believe differently",
                    "Why the market may be wrong",
                    "Which financial line changes if I am correct",
                    "Which catalyst reveals the difference",
                    "What evidence would prove me wrong",
                    "How much can be lost if I am wrong",
                  ].map((x, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-[11px] text-[#a1a1aa]">
                      <span className="w-5 h-5 rounded-full bg-[#3b82f6]/15 text-[#3b82f6] text-[9px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                      {x}
                    </li>
                  ))}
                </ol>
              </Panel>

              <Panel
                title="Every thesis pillar needs a measurable falsifier"
                icon={<XCircle className="w-4 h-4" />}
              >
                <div className="space-y-3">
                  <div className="bg-[#10b981]/5 border border-[#10b981]/20 rounded p-3">
                    <p className="text-[9px] font-bold text-[#10b981] uppercase tracking-wider mb-1">Strong — measurable</p>
                    <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                      “Margin expansion depends on higher capacity utilization and normalized
                      energy costs. The thesis weakens if utilization remains below X% for two
                      consecutive quarters or unit energy cost remains above Y.”
                    </p>
                  </div>
                  <div className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded p-3">
                    <p className="text-[9px] font-bold text-[#ef4444] uppercase tracking-wider mb-1">Weak — unfalsifiable</p>
                    <p className="text-[11px] text-[#71717a] leading-relaxed">
                      “Management is strong and the industry has growth potential.”
                    </p>
                  </div>
                </div>
              </Panel>
            </>
          )}

          {/* ═══ SCORING ════════════════════════════════════════════════ */}
          {section === "scoring" && (
            <>
              <Panel
                title="A. Company Health Score"
                subtitle="Is the underlying business genuinely healthy? Independent of price."
                icon={<Award className="w-4 h-4" />}
              >
                <div className="space-y-1.5">
                  {HEALTH_SCORE.map(c => (
                    <div key={c.component} className="flex items-center justify-between gap-3">
                      <span className="text-[11px] text-[#a1a1aa]">{c.component}</span>
                      <WeightBar weight={c.weight} color="#3b82f6" />
                    </div>
                  ))}
                  <div className="flex items-center justify-between gap-3 pt-2 border-t border-[#27272a]">
                    <span className="text-[11px] font-bold text-[#fafafa]">Total</span>
                    <span className="text-[11px] font-mono font-bold text-[#3b82f6] pr-1">100</span>
                  </div>
                </div>
              </Panel>

              <Panel
                title="B. Stock Attractiveness Score"
                subtitle="Does the current price offer asymmetric risk / reward? Independent of quality."
                icon={<Target className="w-4 h-4" />}
              >
                <div className="space-y-1.5">
                  {ATTRACTIVENESS_SCORE.map(c => (
                    <div key={c.component} className="flex items-center justify-between gap-3">
                      <span className="text-[11px] text-[#a1a1aa]">{c.component}</span>
                      <WeightBar weight={c.weight} color="#10b981" />
                    </div>
                  ))}
                  <div className="flex items-center justify-between gap-3 pt-2 border-t border-[#27272a]">
                    <span className="text-[11px] font-bold text-[#fafafa]">Total</span>
                    <span className="text-[11px] font-mono font-bold text-[#10b981] pr-1">100</span>
                  </div>
                </div>
              </Panel>

              <Panel title="C. Evidence Confidence">
                <div className="space-y-1.5">
                  {EVIDENCE_CONFIDENCE.map(e => (
                    <div key={e.level} className="flex items-center gap-3">
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded w-16 text-center shrink-0"
                        style={{ color: e.color, backgroundColor: `${e.color}15` }}
                      >
                        {e.level}
                      </span>
                      <span className="text-[11px] text-[#a1a1aa]">{e.desc}</span>
                    </div>
                  ))}
                </div>
              </Panel>

              <div className="bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-lg p-4 space-y-1.5">
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  A high-quality company can receive a <span className="text-[#f59e0b] font-bold">low
                  stock-attractiveness score.</span>
                </p>
                <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                  A cheap stock can remain <span className="text-[#f59e0b] font-bold">uninvestable</span>{" "}
                  because governance, solvency or evidence confidence is too weak.
                </p>
              </div>
            </>
          )}

          {/* ═══ PSX SECTOR ENGINES ═════════════════════════════════════ */}
          {section === "sectors" && (
            <Panel
              title="Sector-specific engines for PSX"
              subtitle="The general framework automatically switches to sector-specific KPIs."
              icon={<Factory className="w-4 h-4" />}
            >
              <div className="space-y-2">
                {SECTOR_ENGINES.map(s => (
                  <div key={s.sector} className="bg-[#09090b] border border-[#27272a] rounded p-3 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                      <span className="text-[12px] font-bold" style={{ color: s.color }}>{s.sector}</span>
                      {s.sector === "Fertilizer" && (
                        <span className="text-[8px] px-1.5 py-0.5 rounded bg-[#10b981]/15 text-[#10b981] font-bold uppercase tracking-wider">
                          Pilot
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-[#a1a1aa] leading-snug">{s.drivers}</p>
                    {s.formula && (
                      <code className="block text-[10px] text-[#10b981] font-mono bg-[#18181b] border border-[#27272a] rounded px-2 py-1">
                        {s.formula}
                      </code>
                    )}
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* ═══ DELIVERABLE ════════════════════════════════════════════ */}
          {section === "deliverable" && (
            <>
              <Panel
                title="Final research deliverable"
                subtitle="Twenty-four components in the completed initiation of coverage."
                icon={<ClipboardCheck className="w-4 h-4" />}
              >
                <ol className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1.5">
                  {DELIVERABLE_ITEMS.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#a1a1aa] leading-snug">
                      <span className="w-4 h-4 rounded bg-[#3b82f6]/10 text-[#3b82f6] text-[8px] font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      {item}
                    </li>
                  ))}
                </ol>
              </Panel>

              <Panel title="Final posture — exactly one">
                <div className="space-y-1.5">
                  {FINAL_POSTURES.map(p => (
                    <div key={p.posture} className="flex items-center gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: p.color }} />
                      <span className="text-[11px] font-medium" style={{ color: p.color }}>{p.posture}</span>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel
                title="Default mandate"
                subtitle="If only a company name is provided."
              >
                <div className="bg-[#09090b] border border-[#3b82f6]/30 rounded p-3">
                  <p className="text-[11px] text-[#a1a1aa] leading-relaxed">
                    <span className="text-[#3b82f6] font-bold">Long-only, three-to-five-year
                    fundamental underwrite with a 12-month valuation and catalyst horizon.</span>{" "}
                    Current primary evidence is gathered, market data is time-stamped, and the
                    corporate and subsidiary map is built before any investment conclusion is formed.
                  </p>
                </div>
              </Panel>

              <button
                onClick={() => setSection("run")}
                className="w-full flex items-center justify-center gap-2 py-3 bg-[#3b82f6]/10 border border-[#3b82f6]/30 rounded-lg text-[12px] font-bold text-[#3b82f6] hover:bg-[#3b82f6]/20 transition-colors"
              >
                <Zap className="w-4 h-4" /> Run this framework on a PSX company
              </button>
            </>
          )}

          {/* Footer */}
          <p className="text-center text-[10px] text-[#3f3f46] pt-6 pb-2 leading-relaxed">
            Educational research framework — not investment advice.
            <br />
            Company quality and stock attractiveness are scored separately throughout.
          </p>

        </div>
      </div>
    </div>
  );
}
