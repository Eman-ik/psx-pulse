"use client";

import React from 'react';
import { PSXNewsItem } from './types';
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  BarChart3,
  Sparkles,
  Globe,
  Bot,
  ExternalLink,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

interface NewsDetailModalProps {
  news: PSXNewsItem | null;
  onClose: () => void;
  onAskAgent: (prompt: string) => void;
}

export const NewsDetailModal: React.FC<NewsDetailModalProps> = ({
  news,
  onClose,
  onAskAgent
}) => {
  if (!news) return null;

  const isBull = news.sentiment === 'BULLISH';
  const isBear = news.sentiment === 'BEARISH';

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#0e131f] border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl space-y-6 p-6 font-mono">

        <div className="flex items-start justify-between border-b border-slate-800 pb-4 gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 bg-slate-800 text-slate-300 text-[11px] font-mono font-bold rounded border border-slate-700">
                {news.category.replace('_', ' ')}
              </span>
              {news.geopoliticalRegion && (
                <span className="px-2 py-0.5 bg-slate-900 text-slate-400 text-[10px] font-mono rounded">
                  📍 {news.geopoliticalRegion}
                </span>
              )}
              <span className="text-xs text-slate-400">• {news.source}</span>
            </div>

            <h2 className="text-lg sm:text-xl font-bold text-slate-100 font-mono mt-2 leading-snug">
              {news.title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 transition-all shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-[#121826] border border-slate-800 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 uppercase block">AI SENTIMENT SCORE</span>
            <span
              className={`text-sm font-bold flex items-center ${
                isBull ? 'text-emerald-400' : isBear ? 'text-rose-400' : 'text-slate-300'
              }`}
            >
              {isBull && <TrendingUp className="w-4 h-4 mr-1" />}
              {isBear && <TrendingDown className="w-4 h-4 mr-1" />}
              {!isBull && !isBear && <Minus className="w-4 h-4 mr-1" />}
              {news.sentimentScore > 0 ? `+${news.sentimentScore}` : news.sentimentScore} {news.sentiment}
            </span>
          </div>

          <div className="p-3 bg-[#121826] border border-slate-800 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 uppercase block">VOLATILITY RATING</span>
            <span className="text-sm font-bold text-amber-400">{news.volatilityScore} / 10 Volatility</span>
          </div>

          <div className="p-3 bg-[#121826] border border-slate-800 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 uppercase block">IMPACT HORIZON</span>
            <span className="text-sm font-bold text-slate-200">{news.impactHorizon}</span>
          </div>

          <div className="p-3 bg-[#121826] border border-slate-800 rounded-xl space-y-1">
            <span className="text-[10px] text-slate-400 uppercase block">EXPECTED INDEX DELTA</span>
            <span className="text-sm font-bold text-emerald-400">
              {news.trendProjection?.expectedIndexDelta || '+150 to +300 pts'}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-xs font-bold text-slate-300 uppercase block">AFFECTED PSX EQUITIES & CONSTITUENTS:</span>
          <div className="flex flex-wrap gap-2">
            {news.tickers.map((ticker) => (
              <span
                key={ticker}
                className="px-3 py-1 bg-emerald-950/60 text-emerald-400 border border-emerald-500/40 font-bold rounded-lg text-xs"
              >
                ${ticker}
              </span>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-xs font-bold text-slate-300 uppercase block">EXECUTIVE INTELLIGENCE SUMMARY:</span>
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans bg-[#121826] border border-slate-800 p-4 rounded-xl">
            {news.summary}
          </p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-1.5 text-xs font-bold text-emerald-400 uppercase">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <span>IN-DEPTH FINANCIAL TRANSMISSION & EARNINGS IMPACT:</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans bg-[#121826] border border-slate-800 p-4 rounded-xl">
            {news.aiAnalysis}
          </p>
        </div>

        {news.transmissionPath && (
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-300 uppercase block">STEP-BY-STEP TRANSMISSION CHAIN:</span>
            <div className="space-y-1.5">
              {news.transmissionPath.map((step, idx) => (
                <div key={idx} className="p-2.5 bg-[#121826] border border-slate-800 rounded-lg flex items-center space-x-2 text-xs">
                  <span className="font-bold text-emerald-400">0{idx + 1}.</span>
                  <span className="text-slate-200">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {news.trendProjection && (
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-300 uppercase block">QUANT SCENARIO TREE & PROJECTIONS:</span>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-xl space-y-1">
                <span className="font-bold text-emerald-400 block">BULL CASE ({news.trendProjection.probabilityBull}%)</span>
                <p className="text-slate-300 font-sans text-[11px] leading-relaxed">{news.trendProjection.bullCase}</p>
              </div>

              <div className="p-3 bg-slate-900 border border-slate-700 rounded-xl space-y-1">
                <span className="font-bold text-slate-200 block">BASE CASE</span>
                <p className="text-slate-300 font-sans text-[11px] leading-relaxed">{news.trendProjection.baseCase}</p>
              </div>

              <div className="p-3 bg-rose-950/30 border border-rose-500/30 rounded-xl space-y-1">
                <span className="font-bold text-rose-400 block">BEAR CASE ({news.trendProjection.probabilityBear}%)</span>
                <p className="text-slate-300 font-sans text-[11px] leading-relaxed">{news.trendProjection.bearCase}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
          <button
            onClick={() => {
              onClose();
              onAskAgent(
                `Provide a detailed quantitative trading strategy and recommended position for ${news.tickers.join(', ')} based on news: "${news.title}".`
              );
            }}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center space-x-2 shadow-lg transition-all"
          >
            <Bot className="w-4 h-4" />
            <span>Consult PSX QuantAgent</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold"
          >
            Close Window
          </button>
        </div>

      </div>
    </div>
  );
};
