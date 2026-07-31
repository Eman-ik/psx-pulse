"use client";

import React, { useState } from 'react';
import { PSXNewsItem, NewsCategory, SentimentType } from './types';
import {
  Flame,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Compass,
  ChevronRight,
  Bot,
  ExternalLink,
  ShieldAlert,
  BarChart3,
  Search,
  Filter,
  Sparkles
} from 'lucide-react';

interface LiveNewsTerminalProps {
  newsItems: PSXNewsItem[];
  selectedCategory: NewsCategory;
  setSelectedCategory: (category: NewsCategory) => void;
  selectedSentiment: SentimentType | 'ALL';
  setSelectedSentiment: (sentiment: SentimentType | 'ALL') => void;
  selectedTicker: string | null;
  setSelectedTicker: (ticker: string | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onOpenNewsDetail: (news: PSXNewsItem) => void;
  onAskAgent: (prompt: string) => void;
  isScanningWeb: boolean;
  onTriggerScan: () => void;
}

export const LiveNewsTerminal: React.FC<LiveNewsTerminalProps> = ({
  newsItems,
  selectedCategory,
  setSelectedCategory,
  selectedSentiment,
  setSelectedSentiment,
  selectedTicker,
  setSelectedTicker,
  searchQuery,
  setSearchQuery,
  onOpenNewsDetail,
  onAskAgent,
  isScanningWeb,
  onTriggerScan
}) => {
  const [expandedProjectionId, setExpandedProjectionId] = useState<string | null>(null);

  const popularTickers = ['OGDC', 'PPL', 'SYS', 'MCB', 'LUCK', 'HUBC', 'ENGRO', 'FFC', 'DGKC', 'TRG'];

  const categoriesList: { key: NewsCategory; label: string }[] = [
    { key: 'ALL', label: 'All Intelligence' },
    { key: 'PSX_EQUITIES', label: 'PSX Companies' },
    { key: 'GEOPOLITICS', label: 'Geopolitics' },
    { key: 'MACRO_SBP_IMF', label: 'Macro / SBP / IMF' },
    { key: 'COMMODITIES_FX', label: 'Commodities & FX' },
    { key: 'QUANT_SIGNALS', label: 'Quant Signals' }
  ];

  const filteredItems = newsItems.filter(item => {
    if (selectedCategory !== 'ALL' && item.category !== selectedCategory) return false;
    if (selectedSentiment !== 'ALL' && item.sentiment !== selectedSentiment) return false;
    if (selectedTicker && !item.tickers.includes(selectedTicker)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchSummary = item.summary.toLowerCase().includes(q);
      const matchTickers = item.tickers.some(t => t.toLowerCase().includes(q));
      const matchRegion = item.geopoliticalRegion?.toLowerCase().includes(q);
      if (!matchTitle && !matchSummary && !matchTickers && !matchRegion) return false;
    }
    return true;
  });

  const breakingNews = newsItems.filter(i => i.isBreaking);

  return (
    <div className="space-y-6">

      {breakingNews.length > 0 && (
        <div className="bg-gradient-to-r from-rose-950/80 via-slate-900 to-amber-950/80 border border-rose-500/40 rounded-xl p-3 sm:p-4 flex items-center justify-between gap-4 shadow-lg">
          <div className="flex items-center space-x-3 overflow-hidden">
            <span className="flex items-center space-x-1 px-2.5 py-1 bg-rose-600 text-white font-mono text-[10px] font-bold rounded uppercase tracking-wider shrink-0 animate-pulse">
              <Flame className="w-3.5 h-3.5 fill-white" />
              <span>BREAKING ALERT</span>
            </span>
            <p className="text-xs sm:text-sm font-semibold font-mono text-slate-100 truncate">
              {breakingNews[0].title}
            </p>
          </div>

          <button
            onClick={() => onOpenNewsDetail(breakingNews[0])}
            className="shrink-0 px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-mono font-bold rounded transition-all"
          >
            Inspect Analysis
          </button>
        </div>
      )}

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-4 space-y-4 shadow-sm">

        <div className="flex items-center justify-between border-b border-[#27272a] pb-3 overflow-x-auto gap-2">
          <div className="flex items-center space-x-1.5 min-w-max">
            {categoriesList.map(cat => (
              <button
                key={cat.key}
                onClick={() => setSelectedCategory(cat.key)}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                  selectedCategory === cat.key
                    ? 'bg-[#3b82f6] text-white shadow-xs font-bold'
                    : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] hover:bg-[#27272a] border border-[#27272a]'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="hidden md:flex items-center space-x-2 text-xs font-mono text-[#a1a1aa]">
            <span>Showing {filteredItems.length} items</span>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">

          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono text-[#a1a1aa] uppercase tracking-wider mr-1">
              SENTIMENT:
            </span>
            <button
              onClick={() => setSelectedSentiment('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-mono ${
                selectedSentiment === 'ALL'
                  ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa]'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setSelectedSentiment('BULLISH')}
              className={`px-2.5 py-1 rounded text-xs font-mono flex items-center space-x-1 ${
                selectedSentiment === 'BULLISH'
                  ? 'bg-[#10b981] text-white font-bold'
                  : 'bg-[#10b981]/10 text-[#10b981] hover:bg-[#10b981]/20 border border-[#10b981]/30'
              }`}
            >
              <TrendingUp className="w-3 h-3" />
              <span>Bullish</span>
            </button>
            <button
              onClick={() => setSelectedSentiment('BEARISH')}
              className={`px-2.5 py-1 rounded text-xs font-mono flex items-center space-x-1 ${
                selectedSentiment === 'BEARISH'
                  ? 'bg-[#ef4444] text-white font-bold'
                  : 'bg-[#ef4444]/10 text-[#ef4444] hover:bg-[#ef4444]/20 border border-[#ef4444]/30'
              }`}
            >
              <TrendingDown className="w-3 h-3" />
              <span>Bearish</span>
            </button>
            <button
              onClick={() => setSelectedSentiment('NEUTRAL')}
              className={`px-2.5 py-1 rounded text-xs font-mono flex items-center space-x-1 ${
                selectedSentiment === 'NEUTRAL'
                  ? 'bg-[#27272a] text-white font-bold'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa]'
              }`}
            >
              <Minus className="w-3 h-3" />
              <span>Neutral</span>
            </button>
          </div>

          <div className="flex items-center space-x-1.5 overflow-x-auto scrollbar-none">
            <span className="text-[11px] font-mono text-[#a1a1aa] uppercase tracking-wider shrink-0">
              TICKERS:
            </span>
            {selectedTicker && (
              <button
                onClick={() => setSelectedTicker(null)}
                className="px-2 py-0.5 bg-[#27272a] text-[#fafafa] text-[11px] font-mono rounded hover:bg-[#3f3f46]"
              >
                Clear (${selectedTicker})
              </button>
            )}
            {popularTickers.map(ticker => (
              <button
                key={ticker}
                onClick={() => setSelectedTicker(selectedTicker === ticker ? null : ticker)}
                className={`px-2 py-0.5 text-[11px] font-mono font-bold rounded transition-all shrink-0 ${
                  selectedTicker === ticker
                    ? 'bg-[#3b82f6] text-white shadow-xs'
                    : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] hover:bg-[#27272a] border border-[#27272a]'
                }`}
              >
                ${ticker}
              </button>
            ))}
          </div>

        </div>
      </div>

      <div className="space-y-4">
        {filteredItems.length > 0 ? (
          filteredItems.map(item => {
            const isBull = item.sentiment === 'BULLISH';
            const isBear = item.sentiment === 'BEARISH';
            const isExpanded = expandedProjectionId === item.id;

            return (
              <div
                key={item.id}
                className="bg-[#121214] hover:bg-[#18181b] border border-[#27272a] hover:border-[#3f3f46] rounded-lg p-5 transition-all shadow-xs space-y-4 group relative"
              >

                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#27272a] pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 bg-[#18181b] text-[#fafafa] text-[11px] font-mono font-bold rounded border border-[#27272a]">
                      {item.category.replace('_', ' ')}
                    </span>
                    {item.geopoliticalRegion && (
                      <span className="px-2 py-0.5 bg-[#09090b] text-[#a1a1aa] text-[10px] font-mono rounded border border-[#27272a]">
                        📍 {item.geopoliticalRegion}
                      </span>
                    )}
                    <span className="text-xs font-mono text-[#a1a1aa]">• {item.source}</span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-mono text-[#a1a1aa]">{item.publishedAt}</span>
                    <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 text-[10px] font-mono font-semibold border border-amber-500/30 rounded">
                      VOL {item.volatilityScore}/10
                    </span>
                    <div
                      className={`flex items-center space-x-1 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide border ${
                        isBull
                          ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30'
                          : isBear
                          ? 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30'
                          : 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]'
                      }`}
                    >
                      {isBull && <TrendingUp className="w-3.5 h-3.5" />}
                      {isBear && <TrendingDown className="w-3.5 h-3.5" />}
                      {!isBull && !isBear && <Minus className="w-3.5 h-3.5" />}
                      <span>
                        {item.sentimentScore > 0 ? `+${item.sentimentScore}` : item.sentimentScore}{' '}
                        {item.sentiment}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <h3
                      onClick={() => onOpenNewsDetail(item)}
                      className="text-base sm:text-lg font-semibold font-sans text-[#fafafa] group-hover:text-[#3b82f6] transition-colors cursor-pointer leading-snug"
                    >
                      {item.title}
                    </h3>
                  </div>

                  <p className="text-xs sm:text-sm text-[#a1a1aa] leading-relaxed font-sans">
                    {item.summary}
                  </p>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[11px] font-mono text-[#a1a1aa] mr-1">AFFECTED ASSETS:</span>
                    {item.tickers.map(ticker => (
                      <button
                        key={ticker}
                        onClick={() => setSelectedTicker(ticker)}
                        className="text-xs font-mono font-bold bg-[#18181b] hover:bg-[#3b82f6]/20 text-[#3b82f6] px-2 py-0.5 rounded border border-[#27272a] hover:border-[#3b82f6]/50 transition-all"
                      >
                        ${ticker}
                      </button>
                    ))}
                    <span className="ml-auto text-[10px] font-mono text-[#a1a1aa] bg-[#09090b] px-2 py-0.5 rounded border border-[#27272a]">
                      HORIZON: {item.impactHorizon}
                    </span>
                  </div>
                </div>

                {item.transmissionPath && item.transmissionPath.length > 0 && (
                  <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#3b82f6] font-semibold block">
                      ⚡ FINANCIAL TRANSMISSION PATH:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono text-[#fafafa]">
                      {item.transmissionPath.map((step, idx) => (
                        <div key={idx} className="flex items-center space-x-1.5 bg-[#09090b] p-1.5 rounded border border-[#27272a]">
                          <span className="text-[10px] font-bold text-[#3b82f6] shrink-0">0{idx + 1}.</span>
                          <span className="text-[11px] truncate text-[#a1a1aa]">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {item.trendProjection && (
                  <div>
                    <button
                      onClick={() => setExpandedProjectionId(isExpanded ? null : item.id)}
                      className="w-full flex items-center justify-between py-2 px-3 bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] rounded-lg text-xs font-mono font-semibold text-[#a1a1aa] hover:text-[#fafafa] transition-all"
                    >
                      <div className="flex items-center space-x-2 text-[#3b82f6]">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>QUANT SCENARIO & TREND PROJECTION MODEL</span>
                      </div>
                      <div className="flex items-center space-x-2 text-[#a1a1aa]">
                        <span>Expected Index Delta: <strong className="text-[#fafafa]">{item.trendProjection.expectedIndexDelta}</strong></span>
                        <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="mt-2 bg-[#09090b] border border-[#27272a] rounded-lg p-4 space-y-3 font-mono text-xs">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="p-3 bg-[#10b981]/10 border border-[#10b981]/30 rounded-lg space-y-1">
                            <div className="flex items-center justify-between text-[#10b981] font-bold">
                              <span>BULL CASE ({item.trendProjection.probabilityBull}%)</span>
                            </div>
                            <p className="text-[11px] text-[#fafafa] leading-normal">{item.trendProjection.bullCase}</p>
                          </div>

                          <div className="p-3 bg-[#18181b] border border-[#27272a] rounded-lg space-y-1">
                            <div className="flex items-center justify-between text-[#fafafa] font-bold">
                              <span>BASE CASE</span>
                            </div>
                            <p className="text-[11px] text-[#a1a1aa] leading-normal">{item.trendProjection.baseCase}</p>
                          </div>

                          <div className="p-3 bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-lg space-y-1">
                            <div className="flex items-center justify-between text-[#ef4444] font-bold">
                              <span>BEAR CASE ({item.trendProjection.probabilityBear}%)</span>
                            </div>
                            <p className="text-[11px] text-[#fafafa] leading-normal">{item.trendProjection.bearCase}</p>
                          </div>
                        </div>

                        {item.trendProjection.affectedSectors && (
                          <div className="flex items-center space-x-2 pt-1 text-[11px] text-[#a1a1aa]">
                            <span>Sector Impact Coverage:</span>
                            <div className="flex flex-wrap gap-1">
                              {item.trendProjection.affectedSectors.map(s => (
                                <span key={s} className="px-2 py-0.5 bg-[#18181b] text-[#fafafa] rounded border border-[#27272a]">{s}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#27272a]">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onOpenNewsDetail(item)}
                      className="px-3 py-1.5 bg-[#3b82f6]/10 hover:bg-[#3b82f6]/20 text-[#3b82f6] border border-[#3b82f6]/30 rounded-md text-xs font-mono font-semibold transition-all flex items-center space-x-1.5"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      <span>Deep Analysis</span>
                    </button>

                    <button
                      onClick={() =>
                        onAskAgent(
                          `Provide a deep quantitative analysis of news item: "${item.title}". What is the exact earnings transmission mechanism for ${item.tickers.join(', ')} and recommended trader position?`
                        )
                      }
                      className="px-3 py-1.5 bg-[#18181b] hover:bg-[#27272a] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a] rounded-md text-xs font-mono font-medium transition-all flex items-center space-x-1.5"
                    >
                      <Bot className="w-3.5 h-3.5 text-[#3b82f6]" />
                      <span>Ask QuantAgent</span>
                    </button>
                  </div>

                  <span className="text-[11px] font-mono text-[#a1a1aa]">AI Grounded Evaluation</span>
                </div>

              </div>
            );
          })
        ) : (
          <div className="p-12 bg-[#121214] border border-[#27272a] rounded-lg text-center space-y-4">
            <Compass className="w-12 h-12 text-[#a1a1aa] mx-auto animate-pulse" />
            <h3 className="text-lg font-bold font-mono text-[#fafafa]">No matching intelligence items found</h3>
            <p className="text-xs text-[#a1a1aa] max-w-md mx-auto">
              Try adjusting your category, sentiment, or ticker filter, or run an AI Web Scan to scrape the latest breaking news.
            </p>
            <button
              onClick={onTriggerScan}
              disabled={isScanningWeb}
              className="px-4 py-2 bg-[#3b82f6] hover:bg-blue-600 text-white font-mono text-xs font-bold rounded-md shadow-xs"
            >
              Run AI Web Scan Now
            </button>
          </div>
        )}
      </div>

    </div>
  );
};
