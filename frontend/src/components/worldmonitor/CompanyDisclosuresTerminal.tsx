"use client";

import React, { useState, useEffect } from 'react';
import {
  CompanyDisclosureItem,
  DisclosureCategory
} from './types';
import {
  INITIAL_PSX_DISCLOSURES,
  fetchPSXDisclosuresScraped
} from './data/psxDisclosuresData';
import {
  FileText,
  Search,
  Globe,
  RefreshCw,
  Zap,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Filter,
  ExternalLink,
  Bot,
  CheckCircle2,
  AlertCircle,
  Building2,
  Download,
  Sparkles,
  Layers,
  Calendar,
  X,
  PieChart,
  Terminal
} from 'lucide-react';

interface CompanyDisclosuresTerminalProps {
  onAskAgent?: (promptText: string) => void;
}

export const CompanyDisclosuresTerminal: React.FC<CompanyDisclosuresTerminalProps> = ({ onAskAgent }) => {
  const [disclosures, setDisclosures] = useState<CompanyDisclosureItem[]>(INITIAL_PSX_DISCLOSURES);
  const [selectedTicker, setSelectedTicker] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<DisclosureCategory>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [isScraping, setIsScraping] = useState<boolean>(false);
  const [isLiveScraped, setIsLiveScraped] = useState<boolean>(false);
  const [scrapedAtTime, setScrapedAtTime] = useState<string>('Pre-loaded Portal Data');
  const [groundingSources, setGroundingSources] = useState<{ title: string; uri: string }[]>([]);

  const [scraperLogMessage, setScraperLogMessage] = useState<string>('');
  const [showLogConsole, setShowLogConsole] = useState<boolean>(false);

  const [selectedDisclosure, setSelectedDisclosure] = useState<CompanyDisclosureItem | null>(null);

  const handleTriggerScraper = async () => {
    setIsScraping(true);
    setShowLogConsole(true);
    setScraperLogMessage('Connecting to PSX Data Portal (dps.psx.com.pk)...');

    setTimeout(() => {
      setScraperLogMessage(`Scraping announcements for ${selectedTicker === 'ALL' ? 'All PSX Equities' : selectedTicker}...`);
    }, 600);

    setTimeout(() => {
      setScraperLogMessage('Extracting PDF Financial Statements, EPS figures & Dividend declarations...');
    }, 1200);

    try {
      const result = await fetchPSXDisclosuresScraped(selectedTicker, selectedCategory, searchQuery);

      setDisclosures(result.disclosures);
      setIsLiveScraped(result.isLiveScraped);
      if (result.groundingSources) setGroundingSources(result.groundingSources);
      setScrapedAtTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      setScraperLogMessage(`Web scraping completed successfully! Extracted ${result.disclosures.length} official disclosures.`);
    } catch (err) {
      console.error('Error during PSX Web Scrape:', err);
      setScraperLogMessage('Scraper encountered network timeout. Displaying cached PSX portal disclosures.');
    } finally {
      setTimeout(() => {
        setIsScraping(false);
      }, 1800);
    }
  };

  const filteredDisclosures = disclosures.filter((item) => {
    if (selectedTicker !== 'ALL' && item.ticker.toUpperCase() !== selectedTicker.toUpperCase()) {
      return false;
    }
    if (selectedCategory !== 'ALL' && item.category !== selectedCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        item.title.toLowerCase().includes(q) ||
        item.summary.toLowerCase().includes(q) ||
        item.companyName.toLowerCase().includes(q) ||
        item.ticker.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 font-mono text-xs">

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#27272a] pb-4">
          <div>
            <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-bold uppercase tracking-wider mb-1">
              <Globe className="w-4 h-4 text-[#3b82f6]" />
              <span>PSX CORPORATE ANNOUNCEMENTS & FINANCIAL REPORTS WEB SCRAPER</span>
              <span className="text-[10px] bg-[#3b82f6]/15 text-[#3b82f6] px-2 py-0.5 rounded border border-[#3b82f6]/30">
                dps.psx.com.pk Scraper
              </span>
            </div>
            <h2 className="text-xl font-bold text-[#fafafa] font-mono">
              Live Company Disclosures, Financial Reports & Portal Feed
            </h2>
            <p className="text-[#a1a1aa] text-xs font-sans mt-0.5">
              Automated web-scraping engine parsing quarterly financial reports, EPS results, board meeting outcomes, and dividend declarations straight from official PSX disclosures.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={handleTriggerScraper}
              disabled={isScraping}
              className="px-4 py-2 bg-[#3b82f6] hover:bg-blue-600 text-white font-mono font-bold text-xs rounded transition-all flex items-center justify-center space-x-2 cursor-pointer shadow-md disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isScraping ? 'animate-spin' : ''}`} />
              <span>{isScraping ? 'Scraping PSX Portal...' : 'Scrape PSX Portal Live'}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-[#18181b] p-4 rounded-lg border border-[#27272a]">

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
              Company Ticker
            </label>
            <select
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
            >
              <option value="ALL">ALL PSX COMPANIES</option>
              <option value="OGDC">$OGDC - Oil & Gas Dev</option>
              <option value="PPL">$PPL - Pak Petroleum</option>
              <option value="SYS">$SYS - Systems Limited</option>
              <option value="LUCK">$LUCK - Lucky Cement</option>
              <option value="MCB">$MCB - MCB Bank</option>
              <option value="HUBC">$HUBC - Hub Power</option>
              <option value="ENGRO">$ENGRO - Engro Corp</option>
              <option value="FFC">$FFC - Fauji Fertilizer</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
              Disclosure Type
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as DisclosureCategory)}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
            >
              <option value="ALL">ALL DISCLOSURE CATEGORIES</option>
              <option value="FINANCIAL_RESULTS">Financial Results & EPS</option>
              <option value="BOARD_MEETING">Board Meeting Outcomes</option>
              <option value="DIVIDEND_DECLARATION">Dividends & Bonus Shares</option>
              <option value="MATERIAL_INFORMATION">Material Corporate Information</option>
            </select>
          </div>

          <div className="space-y-1 sm:col-span-2">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
              Search Filing Keywords
            </label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#a1a1aa]" />
              <input
                type="text"
                placeholder="e.g. EPS, Dividend, Gas Discovery, Expansion, Revenue..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded pl-8 pr-3 py-1.5 text-xs font-mono outline-none"
              />
            </div>
          </div>

        </div>

        {showLogConsole && (
          <div className="bg-[#09090b] border border-[#27272a] rounded-lg p-3 space-y-1 text-[11px] font-mono text-[#a1a1aa] relative">
            <div className="flex items-center justify-between text-xs text-[#fafafa] border-b border-[#27272a] pb-1.5 mb-1.5">
              <span className="flex items-center gap-1.5 font-bold text-[#3b82f6]">
                <Terminal className="w-3.5 h-3.5 text-[#3b82f6]" />
                PSX SCRAPER ENGINE LIVE CONSOLE OUTPUT
              </span>
              <button
                onClick={() => setShowLogConsole(false)}
                className="text-[#a1a1aa] hover:text-[#fafafa]"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="flex items-center space-x-2 text-[#10b981]">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-ping" />
              <span>{scraperLogMessage}</span>
            </div>
            <p className="text-[10px] text-[#71717a]">
              Last scraped timestamp: {scrapedAtTime} | Mode: {isLiveScraped ? 'Grounded Live PSX Search' : 'Cached Official PSX Disclosures'}
            </p>
          </div>
        )}
      </div>

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-bold text-[#fafafa] text-xs flex items-center gap-2">
            <PieChart className="w-4 h-4 text-[#10b981]" />
            RECENT SCRAPED FINANCIAL RESULTS & EPS MATRIX
          </span>
          <span className="text-[10px] text-[#a1a1aa]">Official Audited & Unaudited Statements</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-[11px]">
            <thead>
              <tr className="border-b border-[#27272a] bg-[#18181b] text-[#a1a1aa] uppercase text-[9px] tracking-wider">
                <th className="p-2.5">Ticker & Company</th>
                <th className="p-2.5">Period</th>
                <th className="p-2.5">Revenue (PKR B)</th>
                <th className="p-2.5">Net Profit (PKR B)</th>
                <th className="p-2.5">EPS (PKR)</th>
                <th className="p-2.5">Cash Dividend</th>
                <th className="p-2.5">YoY Profit Growth</th>
                <th className="p-2.5">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#27272a] text-[#fafafa]">
              {disclosures
                .filter(d => d.financialMetrics && d.financialMetrics.epsPkr > 0)
                .map((d) => {
                  const m = d.financialMetrics!;
                  const isPos = m.yoyNetProfitGrowthPct >= 0;
                  return (
                    <tr key={`matrix-${d.id}`} className="hover:bg-[#18181b] transition-all">
                      <td className="p-2.5">
                        <span className="font-bold text-[#3b82f6] mr-1.5">${d.ticker}</span>
                        <span className="text-[#a1a1aa] text-[10px] hidden sm:inline">{d.companyName}</span>
                      </td>
                      <td className="p-2.5">
                        <span className="px-1.5 py-0.5 bg-[#27272a] text-[#fafafa] rounded text-[10px]">
                          {m.period}
                        </span>
                      </td>
                      <td className="p-2.5 font-bold">PKR {m.revenuePkrBillion}B</td>
                      <td className="p-2.5 font-bold">PKR {m.netProfitPkrBillion}B</td>
                      <td className="p-2.5 font-bold text-[#10b981]">PKR {m.epsPkr.toFixed(2)}</td>
                      <td className="p-2.5">
                        {m.cashDividendPkrPerShare ? (
                          <span className="font-bold text-[#10b981]">PKR {m.cashDividendPkrPerShare.toFixed(2)}/sh</span>
                        ) : (
                          <span className="text-[#71717a]">Nil</span>
                        )}
                      </td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isPos ? 'bg-[#10b981]/15 text-[#10b981]' : 'bg-[#ef4444]/15 text-[#ef4444]'
                        }`}>
                          {isPos ? `+${m.yoyNetProfitGrowthPct}%` : `${m.yoyNetProfitGrowthPct}%`}
                        </span>
                      </td>
                      <td className="p-2.5">
                        <button
                          onClick={() => setSelectedDisclosure(d)}
                          className="px-2 py-1 bg-[#3b82f6]/15 hover:bg-[#3b82f6]/25 text-[#3b82f6] border border-[#3b82f6]/30 rounded text-[10px] font-bold flex items-center gap-1 transition-all"
                        >
                          <FileText className="w-3 h-3" />
                          <span>View Report</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-[#fafafa] flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#3b82f6]" />
            OFFICIAL PSX DISCLOSURES & CORPORATE FILINGS ({filteredDisclosures.length})
          </span>
          <span className="text-[10px] text-[#a1a1aa]">Updated Real-Time via PSX Data Scraper</span>
        </div>

        {filteredDisclosures.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {filteredDisclosures.map((item) => {
              const isBull = item.sentiment === 'BULLISH';
              return (
                <div
                  key={item.id}
                  className="bg-[#121214] border border-[#27272a] hover:border-[#3b82f6] transition-all rounded-lg p-4 space-y-3 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#27272a] pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/30 rounded font-bold text-xs">
                        ${item.ticker}
                      </span>
                      <span className="font-bold text-[#fafafa] text-xs font-sans">
                        {item.companyName}
                      </span>
                      <span className="text-[10px] text-[#a1a1aa] hidden md:inline">
                        • {item.sector}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        item.category === 'FINANCIAL_RESULTS'
                          ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                          : item.category === 'DIVIDEND_DECLARATION'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                      }`}>
                        {item.category.replace('_', ' ')}
                      </span>

                      <span className="text-[10px] text-[#a1a1aa] flex items-center gap-1 font-mono">
                        <Calendar className="w-3 h-3" />
                        {item.publishedAt}
                      </span>
                    </div>
                  </div>

                  <h3 className="text-sm font-bold text-[#fafafa] font-sans">
                    {item.title}
                  </h3>

                  {item.financialMetrics && item.financialMetrics.epsPkr > 0 && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#18181b] p-2.5 rounded border border-[#27272a] text-center">
                      <div>
                        <span className="text-[9px] text-[#a1a1aa] block">PERIOD</span>
                        <span className="text-xs font-bold text-[#fafafa]">{item.financialMetrics.period}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[#a1a1aa] block">REVENUE</span>
                        <span className="text-xs font-bold text-[#fafafa]">PKR {item.financialMetrics.revenuePkrBillion}B</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[#a1a1aa] block">NET PROFIT / EPS</span>
                        <span className="text-xs font-bold text-[#10b981]">
                          PKR {item.financialMetrics.epsPkr.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[#a1a1aa] block">DIVIDEND DECLARED</span>
                        <span className="text-xs font-bold text-[#10b981]">
                          {item.financialMetrics.cashDividendPkrPerShare ? `PKR ${item.financialMetrics.cashDividendPkrPerShare.toFixed(2)}` : 'Nil'}
                        </span>
                      </div>
                    </div>
                  )}

                  <p className="text-xs text-[#a1a1aa] font-sans leading-relaxed">
                    {item.summary}
                  </p>

                  <div className="bg-[#18181b] p-2.5 rounded border-l-2 border-[#3b82f6] text-[11px] text-[#a1a1aa] space-y-1 font-sans">
                    <span className="font-bold text-[#3b82f6] flex items-center gap-1 text-[10px]">
                      <Sparkles className="w-3 h-3" />
                      QUANT IMPACT & REVISION ANALYSIS
                    </span>
                    <p>{item.impactNote}</p>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-2 border-t border-[#27272a]">
                    <div className="flex items-center space-x-2 text-[10px] text-[#a1a1aa]">
                      <span>Source: PSX Data Portal</span>
                      {item.sourceUrl && (
                        <a
                          href={item.sourceUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#3b82f6] hover:underline flex items-center gap-0.5"
                        >
                          <span>dps.psx.com.pk</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedDisclosure(item)}
                        className="px-3 py-1.5 bg-[#27272a] hover:bg-[#3f3f46] text-[#fafafa] font-bold text-xs rounded transition-all flex items-center space-x-1"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Read Full Statement</span>
                      </button>

                      <button
                        onClick={() => {
                          if (onAskAgent) {
                            onAskAgent(`QuantAgent, analyze official PSX disclosure for $${item.ticker} (${item.companyName}): "${item.title}". Summary: ${item.summary}. What is the revised valuation model, target price, and EPS forecast impact?`);
                          }
                        }}
                        className="px-3 py-1.5 bg-[#10b981] hover:bg-[#059669] text-white font-bold text-xs rounded transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
                      >
                        <Bot className="w-3.5 h-3.5" />
                        <span>Ask QuantAgent</span>
                      </button>
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-[#121214] border border-[#27272a] rounded-lg p-12 text-center text-[#a1a1aa] space-y-3">
            <AlertCircle className="w-8 h-8 text-[#a1a1aa] mx-auto" />
            <p className="text-sm font-bold text-[#fafafa]">No company disclosures matched your current search filters.</p>
            <p className="text-xs">Try selecting 'ALL PSX COMPANIES' or click 'Scrape PSX Portal Live' above.</p>
          </div>
        )}
      </div>

      {selectedDisclosure && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121214] border border-[#27272a] rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-2xl relative font-mono text-xs max-h-[90vh] overflow-y-auto">

            <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-[#3b82f6]/10 border border-[#3b82f6]/30 text-[#3b82f6] rounded-lg">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#3b82f6]">${selectedDisclosure.ticker}</span>
                    <span className="text-[#a1a1aa]">• {selectedDisclosure.sector}</span>
                  </div>
                  <h3 className="text-base font-bold text-[#fafafa] font-sans">
                    {selectedDisclosure.companyName}
                  </h3>
                </div>
              </div>

              <button
                onClick={() => setSelectedDisclosure(null)}
                className="text-[#a1a1aa] hover:text-[#fafafa] p-1.5 rounded-full hover:bg-[#27272a]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] bg-[#3b82f6]/20 text-[#3b82f6] border border-[#3b82f6]/30 px-2 py-0.5 rounded font-bold uppercase">
                  {selectedDisclosure.category.replace('_', ' ')}
                </span>
                <span className="text-[10px] text-[#a1a1aa]">{selectedDisclosure.publishedAt}</span>
              </div>
              <h4 className="text-base font-bold text-[#fafafa] font-sans">
                {selectedDisclosure.title}
              </h4>
            </div>

            {selectedDisclosure.financialMetrics && selectedDisclosure.financialMetrics.epsPkr > 0 && (
              <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 space-y-3">
                <span className="font-bold text-[#10b981] text-xs block">
                  FINANCIAL STATEMENT BREAKDOWN ({selectedDisclosure.financialMetrics.period})
                </span>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">REVENUE</span>
                    <span className="text-sm font-extrabold text-[#fafafa]">
                      PKR {selectedDisclosure.financialMetrics.revenuePkrBillion}B
                    </span>
                    <span className="text-[9px] text-[#10b981] block mt-0.5">
                      +{selectedDisclosure.financialMetrics.yoyRevenueGrowthPct}% YoY
                    </span>
                  </div>

                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">NET PROFIT</span>
                    <span className="text-sm font-extrabold text-[#10b981]">
                      PKR {selectedDisclosure.financialMetrics.netProfitPkrBillion}B
                    </span>
                    <span className="text-[9px] text-[#10b981] block mt-0.5">
                      +{selectedDisclosure.financialMetrics.yoyNetProfitGrowthPct}% YoY
                    </span>
                  </div>

                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">EARNINGS PER SHARE</span>
                    <span className="text-sm font-extrabold text-[#3b82f6]">
                      PKR {selectedDisclosure.financialMetrics.epsPkr.toFixed(2)}
                    </span>
                  </div>

                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">GROSS MARGIN</span>
                    <span className="text-sm font-extrabold text-[#fafafa]">
                      {selectedDisclosure.financialMetrics.grossMarginPct}%
                    </span>
                  </div>

                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">NET MARGIN</span>
                    <span className="text-sm font-extrabold text-[#fafafa]">
                      {selectedDisclosure.financialMetrics.netMarginPct}%
                    </span>
                  </div>

                  <div className="bg-[#121214] p-2.5 rounded border border-[#27272a]">
                    <span className="text-[9px] text-[#a1a1aa] block">CASH DIVIDEND</span>
                    <span className="text-sm font-extrabold text-[#10b981]">
                      {selectedDisclosure.financialMetrics.cashDividendPkrPerShare ? `PKR ${selectedDisclosure.financialMetrics.cashDividendPkrPerShare.toFixed(2)}` : 'Nil'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="font-bold text-[#fafafa] text-xs block">
                OFFICIAL SCRAPED FILING TEXT
              </span>
              <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 font-sans text-xs text-[#a1a1aa] leading-relaxed whitespace-pre-line max-h-60 overflow-y-auto">
                {selectedDisclosure.fullBodyText || selectedDisclosure.summary}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-[#27272a]">
              <a
                href={selectedDisclosure.sourceUrl || 'https://dps.psx.com.pk/announcements'}
                target="_blank"
                rel="noreferrer"
                className="text-[#3b82f6] hover:underline flex items-center gap-1.5 text-xs font-bold"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Open Document on PSX Portal (dps.psx.com.pk)</span>
              </a>

              <button
                onClick={() => {
                  const item = selectedDisclosure;
                  setSelectedDisclosure(null);
                  if (onAskAgent) {
                    onAskAgent(`QuantAgent, analyze $${item.ticker} financial report (${item.title}). Summary: ${item.summary}. What are the long-term target revisions and buy/hold/sell recommendations?`);
                  }
                }}
                className="w-full sm:w-auto px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-white font-mono font-bold text-xs rounded transition-all flex items-center justify-center space-x-2 cursor-pointer shadow-md"
              >
                <Bot className="w-4 h-4" />
                <span>Ask QuantAgent to Analyze Report</span>
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
