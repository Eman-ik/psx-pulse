"use client";

import React, { useState, useMemo } from 'react';
import {
  CompanyDisclosureItem,
  DisclosureCategory,
  SentimentType
} from './types';
import type { NewsAnnouncement } from '@/lib/api';

import {
  FileText,
  Search,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Calendar,
  X,
  Database,
} from 'lucide-react';

function convertDbAnnouncement(
  a: NewsAnnouncement,
  companyById: Record<number, { name: string; symbol: string | null }>
): CompanyDisclosureItem {
  const company = a.issuer_id != null ? companyById[a.issuer_id] : null;
  const ticker = company?.symbol ?? 'PSX';
  const companyName = company?.name ?? 'PSX Listed Company';
  const categoryMap: Record<string, DisclosureCategory> = {
    payout: 'DIVIDEND_DECLARATION',
    results: 'FINANCIAL_RESULTS',
    leadership: 'BOARD_MEETING',
    regulatory: 'MATERIAL_INFORMATION',
    operations: 'MATERIAL_INFORMATION',
    general: 'MATERIAL_INFORMATION',
  };
  const category: DisclosureCategory = categoryMap[a.category] ?? 'MATERIAL_INFORMATION';
  const score = a.sentiment_score ?? 0;
  const sentiment: SentimentType = score > 0.2 ? 'BULLISH' : score < -0.2 ? 'BEARISH' : 'NEUTRAL';
  return {
    id: `db-${a.id}`,
    ticker,
    companyName,
    sector: 'Fertilizer',
    title: a.title,
    category,
    publishedAt: a.published_at.slice(0, 10),
    sourceUrl: a.source_url ?? undefined,
    summary: a.summary ?? 'PSX corporate announcement filed with the Exchange.',
    sentiment,
    sentimentScore: Math.round(Math.abs(score) * 100),
    impactNote: `Official PSX filing by ${companyName} (${ticker}). Category: ${a.category}. Sentiment score based on headline keyword analysis.`,
    isScrapedLive: false,
  };
}

interface CompanyDisclosuresTerminalProps {
  onAskAgent?: (promptText: string) => void;
  realAnnouncements?: NewsAnnouncement[];
  companyById?: Record<number, { name: string; symbol: string | null }>;
}

export const CompanyDisclosuresTerminal: React.FC<CompanyDisclosuresTerminalProps> = ({
  onAskAgent,
  realAnnouncements = [],
  companyById = {},
}) => {
  const allDisclosures = useMemo(
    () => realAnnouncements
      .map((a) => convertDbAnnouncement(a, companyById))
      .sort((a, b) => b.publishedAt.localeCompare(a.publishedAt)),
    [realAnnouncements, companyById]
  );

  const [selectedTicker, setSelectedTicker] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<DisclosureCategory>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDisclosure, setSelectedDisclosure] = useState<CompanyDisclosureItem | null>(null);

  // Derive available tickers from real data only
  const availableTickers = useMemo(() => {
    const tickers = new Set<string>();
    allDisclosures.forEach(d => tickers.add(d.ticker));
    return Array.from(tickers).sort();
  }, [allDisclosures]);

  const filteredDisclosures = allDisclosures.filter((item) => {
    if (selectedTicker !== 'ALL' && item.ticker !== selectedTicker) return false;
    if (selectedCategory !== 'ALL' && item.category !== selectedCategory) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      if (
        !item.title.toLowerCase().includes(q) &&
        !item.summary.toLowerCase().includes(q) &&
        !item.companyName.toLowerCase().includes(q) &&
        !item.ticker.toLowerCase().includes(q)
      ) return false;
    }
    return true;
  });

  const categoryLabel: Record<DisclosureCategory, string> = {
    ALL: 'All Categories',
    FINANCIAL_RESULTS: 'Financial Results',
    BOARD_MEETING: 'Board Meeting',
    DIVIDEND_DECLARATION: 'Dividends',
    MATERIAL_INFORMATION: 'Material Information',
    DIRECTORS_SHAREHOLDING: 'Directors Shareholding',
  };

  return (
    <div className="space-y-6 font-mono text-xs">

      {/* Header */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#27272a] pb-4">
          <div>
            <div className="flex items-center space-x-2 text-[#10b981] text-xs font-bold uppercase tracking-wider mb-1">
              <Database className="w-4 h-4" />
              <span>PSX OFFICIAL ANNOUNCEMENTS — FERTILIZER SECTOR PILOT</span>
              <span className="text-[10px] bg-[#10b981]/15 text-[#10b981] px-2 py-0.5 rounded border border-[#10b981]/30">
                {allDisclosures.length} real filings
              </span>
            </div>
            <h2 className="text-xl font-bold text-[#fafafa] font-mono">
              Corporate Disclosures & Filings
            </h2>
            <p className="text-[#a1a1aa] text-xs font-sans mt-0.5">
              Official PSX announcements for FFC, EFERT, FATIMA, AGL, AHCL — ingested from PSX announcements feed and stored in the research DB. Sentiment scored by headline keyword analysis (not AI/LLM).
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-[#18181b] p-4 rounded-lg border border-[#27272a]">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">Company</label>
            <select
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
            >
              <option value="ALL">All Companies</option>
              {availableTickers.map(t => (
                <option key={t} value={t}>${t}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as DisclosureCategory)}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
            >
              <option value="ALL">All Categories</option>
              <option value="FINANCIAL_RESULTS">Financial Results</option>
              <option value="BOARD_MEETING">Board Meeting</option>
              <option value="DIVIDEND_DECLARATION">Dividends</option>
              <option value="MATERIAL_INFORMATION">Material Information</option>
            </select>
          </div>

          <div className="space-y-1 sm:col-span-2">
            <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">Search</label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#a1a1aa]" />
              <input
                type="text"
                placeholder="EPS, Dividend, Urea, AGM..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded pl-8 pr-3 py-1.5 text-xs font-mono outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Disclosures list */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-[#10b981] flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            {filteredDisclosures.length} of {allDisclosures.length} ANNOUNCEMENTS
          </span>
          <span className="text-[10px] text-[#a1a1aa]">Ingested from official PSX announcements feed · Sorted by date</span>
        </div>

        {filteredDisclosures.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {filteredDisclosures.map((item) => (
              <div
                key={item.id}
                className="bg-[#121214] border border-[#27272a] hover:border-[#3b82f6]/50 rounded-lg p-4 space-y-2 shadow-xs transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30 rounded font-bold text-xs">
                      ${item.ticker}
                    </span>
                    <span className="font-semibold text-[#fafafa] text-xs font-sans">{item.companyName}</span>
                    <span className="text-[10px] bg-[#18181b] border border-[#27272a] px-1.5 py-0.5 rounded text-[#a1a1aa] font-mono uppercase hidden sm:inline">
                      {categoryLabel[item.category]}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      item.sentiment === 'BULLISH' ? 'bg-[#10b981]/15 text-[#10b981]' :
                      item.sentiment === 'BEARISH' ? 'bg-[#ef4444]/15 text-[#ef4444]' :
                      'bg-[#27272a] text-[#a1a1aa]'
                    }`}>
                      {item.sentiment}
                    </span>
                    <span className="text-[10px] text-[#a1a1aa] font-mono flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {item.publishedAt}
                    </span>
                  </div>
                </div>

                <h3 className="text-sm text-[#fafafa] font-sans leading-snug">{item.title}</h3>
                <p className="text-xs text-[#a1a1aa] font-sans leading-relaxed">{item.summary}</p>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-[10px] text-[#71717a] font-mono">
                    Keyword sentiment · not an AI/LLM signal
                  </span>
                  <div className="flex items-center gap-2">
                    {item.sourceUrl && (
                      <a href={item.sourceUrl} target="_blank" rel="noreferrer"
                        className="text-[#3b82f6] hover:underline flex items-center gap-0.5 text-[10px] font-mono">
                        <ExternalLink className="w-3 h-3" />
                        Source
                      </a>
                    )}
                    <button
                      onClick={() => setSelectedDisclosure(item)}
                      className="px-2 py-1 bg-[#27272a] hover:bg-[#3f3f46] text-[#fafafa] text-[10px] rounded flex items-center gap-1 transition-all"
                    >
                      <FileText className="w-3 h-3" />
                      Detail
                    </button>
                    {onAskAgent && (
                      <button
                        onClick={() => onAskAgent(`Analyze this PSX announcement for $${item.ticker}: "${item.title}". Summary: ${item.summary}. What does this mean for the company?`)}
                        className="px-2 py-1 bg-[#3b82f6]/15 hover:bg-[#3b82f6]/25 text-[#3b82f6] border border-[#3b82f6]/30 text-[10px] rounded flex items-center gap-1 transition-all"
                      >
                        Ask AI
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[#121214] border border-[#27272a] rounded-lg p-12 text-center text-[#a1a1aa] space-y-3">
            <AlertCircle className="w-8 h-8 text-[#a1a1aa] mx-auto" />
            <p className="text-sm font-bold text-[#fafafa]">No announcements matched your filters.</p>
            <p className="text-xs">Try selecting &apos;All Companies&apos; or clearing the search.</p>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedDisclosure && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121214] border border-[#27272a] rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-2xl relative font-mono text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-bold text-[#10b981]">${selectedDisclosure.ticker}</span>
                  <span className="text-[#a1a1aa]">· {selectedDisclosure.companyName}</span>
                </div>
                <span className="text-[10px] bg-[#27272a] text-[#a1a1aa] px-2 py-0.5 rounded uppercase">
                  {categoryLabel[selectedDisclosure.category]}
                </span>
              </div>
              <button onClick={() => setSelectedDisclosure(null)} className="text-[#a1a1aa] hover:text-[#fafafa] p-1.5 rounded-full hover:bg-[#27272a]">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <h4 className="text-sm font-bold text-[#fafafa] font-sans mb-3">{selectedDisclosure.title}</h4>
              <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 font-sans text-xs text-[#a1a1aa] leading-relaxed">
                {selectedDisclosure.summary}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-[#27272a]">
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-[#71717a]">{selectedDisclosure.publishedAt}</span>
                {selectedDisclosure.sourceUrl && (
                  <a href={selectedDisclosure.sourceUrl} target="_blank" rel="noreferrer"
                    className="text-[#3b82f6] hover:underline flex items-center gap-1.5 text-xs font-bold">
                    <ExternalLink className="w-4 h-4" />
                    Open on PSX Portal
                  </a>
                )}
              </div>
              {onAskAgent && (
                <button
                  onClick={() => {
                    const item = selectedDisclosure;
                    setSelectedDisclosure(null);
                    onAskAgent(`Analyze this PSX disclosure for $${item.ticker} (${item.companyName}): "${item.title}". ${item.summary}`);
                  }}
                  className="px-4 py-2 bg-[#3b82f6] hover:bg-blue-600 text-white font-mono font-bold text-xs rounded transition-all flex items-center gap-2"
                >
                  Ask QuantAgent
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
