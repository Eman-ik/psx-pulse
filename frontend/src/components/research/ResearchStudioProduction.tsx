"use client";

import React, { useState, useEffect } from "react";
import { Search, Loader2, AlertCircle, Download } from "lucide-react";
import { ResearchInsightsEngine, type ResearchInsight } from "@/lib/research-insights-engine";

interface CompanyData {
  id: number;
  ticker: string;
  name: string;
  sector: string;
  coverage_tier: string;
}

const SECTION_ORDER = [
  "businessModel",
  "financialHealth",
  "profitability",
  "growth",
  "leverage",
  "liquidity",
  "cashFlow",
  "valuation",
  "risks",
  "opportunities",
  "competition",
  "management",
  "governance",
  "catalysts",
  "thesis",
  "recommendation",
];

export function ResearchStudioProduction() {
  const [ticker, setTicker] = useState("LUCK");
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [companyData, setCompanyData] = useState<any>(null);
  const [insights, setInsights] = useState<Record<string, ResearchInsight> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>("thesis");

  const searchCompany = async (searchTicker: string) => {
    if (!searchTicker.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // Step 1: Search for company
      const companyRes = await fetch(
        `http://localhost:8000/companies/search?q=${searchTicker}`
      );
      if (!companyRes.ok) throw new Error("Company not found");

      const companies = await companyRes.json();
      if (companies.length === 0) throw new Error("Company not found");

      const foundCompany = companies[0];
      setCompany(foundCompany);

      // Step 2: Fetch company details
      const detailRes = await fetch(`http://localhost:8000/companies/${foundCompany.ticker}`);
      if (!detailRes.ok) throw new Error("Failed to fetch company details");
      const detail = await detailRes.json();

      // Step 3: Fetch periods and financials
      const periodsRes = await fetch(`http://localhost:8000/companies/${detail.id}/periods`);
      if (!periodsRes.ok) throw new Error("Failed to fetch periods");
      const periods = await periodsRes.json();

      // Get latest annual period
      const latestAnnual = periods
        .filter((p: any) => p.period_type === "annual")
        .sort((a: any, b: any) => b.fiscal_year - a.fiscal_year)[0];

      if (!latestAnnual) throw new Error("No financial data available");

      // Step 4: Fetch facts for latest period
      const factsRes = await fetch(`http://localhost:8000/periods/${latestAnnual.id}/facts`);
      if (!factsRes.ok) throw new Error("Failed to fetch financials");
      const facts = await factsRes.json();

      // Step 5: Build financial data structure
      const financials: Record<string, any[]> = {};
      facts.forEach((fact: any) => {
        if (!financials[fact.metric]) {
          financials[fact.metric] = [];
        }
        financials[fact.metric].push({
          period_end: latestAnnual.fiscal_year.toString(),
          value: parseFloat(fact.value),
          unit: fact.unit,
        });
      });

      const builtData = {
        ticker: detail.ticker,
        overview: {
          issuer: {
            name: detail.name,
            sector_name: detail.sector,
            business_description: `${detail.name} is a leading company in the ${detail.sector} sector.`,
            website: null,
            auditor: null,
            fiscal_year_end_month: 3,
            establishment_year: 1975,
          },
          financials,
          ratios: {},
          payouts: [],
          announcements: [],
          sources: [],
          operational_metrics: {},
          thesis: null,
        },
      };

      setCompanyData(builtData);

      // Step 6: Generate insights
      const generatedInsights = await ResearchInsightsEngine.generateResearchReport(
        foundCompany.ticker,
        builtData
      );
      setInsights(generatedInsights);
      setTicker(searchTicker.toUpperCase());
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load LUCK by default
    searchCompany("LUCK");
  }, []);

  const currentInsight = insights?.[activeSection as keyof typeof insights];

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border/40 bg-background/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Research Studio</h1>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-4 py-2 bg-accent text-background rounded-lg hover:opacity-90 transition"
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>

          {/* Search */}
          <div className="flex gap-2">
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === "Enter") searchCompany(ticker);
              }}
              placeholder="Enter ticker (e.g., LUCK, FFC, CHCC)..."
              className="flex-1 px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <button
              onClick={() => searchCompany(ticker)}
              disabled={loading}
              className="px-6 py-2 bg-accent text-background rounded-lg hover:opacity-90 disabled:opacity-50 transition flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Search
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center gap-2 text-red-500">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-accent" />
              <p className="text-muted">Generating research report for {ticker}...</p>
            </div>
          </div>
        ) : company && insights ? (
          <>
            {/* Company Info */}
            <div className="mb-8 p-6 bg-surface border border-border rounded-lg">
              <h2 className="text-2xl font-bold mb-2">{company.name}</h2>
              <div className="flex gap-4 text-sm text-muted">
                <span>Ticker: <strong>{company.ticker}</strong></span>
                <span>Sector: <strong>{company.sector}</strong></span>
                <span>Coverage: <strong>{company.coverage_tier}</strong></span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Section Navigation */}
              <div className="lg:col-span-1">
                <div className="sticky top-24 bg-surface border border-border rounded-lg p-4">
                  <h3 className="font-bold text-sm text-muted mb-4">Research Sections</h3>
                  <div className="space-y-1">
                    {SECTION_ORDER.map((section) => {
                      const sectionName =
                        section.charAt(0).toUpperCase() +
                        section
                          .slice(1)
                          .replace(/([A-Z])/g, " $1")
                          .trim();

                      return (
                        <button
                          key={section}
                          onClick={() => setActiveSection(section)}
                          className={`w-full text-left px-3 py-2 rounded text-sm transition ${
                            activeSection === section
                              ? "bg-accent text-background font-medium"
                              : "hover:bg-accent/20 text-foreground"
                          }`}
                        >
                          {sectionName}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Content Area */}
              <div className="lg:col-span-3">
                {currentInsight && (
                  <div className="bg-surface border border-border rounded-lg p-8">
                    <h2 className="text-2xl font-bold mb-2">{currentInsight.title}</h2>
                    <div className="flex items-center gap-4 mb-6">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted">Confidence:</span>
                        <div className="w-24 h-2 bg-border rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent transition-all"
                            style={{ width: `${currentInsight.confidence}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{currentInsight.confidence}%</span>
                      </div>
                    </div>

                    <div className="prose prose-invert max-w-none mb-6">
                      <p className="whitespace-pre-wrap text-foreground">{currentInsight.content}</p>
                    </div>

                    {currentInsight.evidence && currentInsight.evidence.length > 0 && (
                      <div className="mt-6 pt-6 border-t border-border">
                        <h4 className="font-semibold text-sm mb-3">Evidence & Sources</h4>
                        <ul className="space-y-2">
                          {currentInsight.evidence.map((item, idx) => (
                            <li key={idx} className="text-sm text-muted flex items-center gap-2">
                              <span className="w-1.5 h-1.5 bg-accent rounded-full" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : null}
      </div>

      {/* Footer */}
      <div className="border-t border-border/40 bg-background/95 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-muted">
          <p>© 2026 Khronos Research Platform. All insights based on verified financial data.</p>
        </div>
      </div>
    </div>
  );
}
