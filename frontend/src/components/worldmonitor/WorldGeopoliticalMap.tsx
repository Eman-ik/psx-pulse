"use client";

import React, { useState } from 'react';
import { MapHotspot, PSXNewsItem } from './types';
import { Globe, AlertTriangle, ArrowRight, ShieldAlert, Cpu, ExternalLink, Zap } from 'lucide-react';

interface WorldGeopoliticalMapProps {
  hotspots: MapHotspot[];
  newsItems: PSXNewsItem[];
  onSelectHotspotNewsFilter: (regionName: string) => void;
  onOpenNewsDetail: (news: PSXNewsItem) => void;
}

export const WorldGeopoliticalMap: React.FC<WorldGeopoliticalMapProps> = ({
  hotspots,
  newsItems,
  onSelectHotspotNewsFilter,
  onOpenNewsDetail
}) => {
  const [selectedHotspot, setSelectedHotspot] = useState<MapHotspot>(hotspots[0] || null);

  const relatedNews = selectedHotspot
    ? newsItems.filter(
        item =>
          item.geopoliticalRegion?.toLowerCase().includes(selectedHotspot.region.toLowerCase()) ||
          item.tickers.some(t => selectedHotspot.affectedTickers.includes(t))
      )
    : [];

  return (
    <div className="space-y-6">

      <div className="bg-[#0e131f] border border-slate-800 rounded-xl p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 font-mono text-xs font-semibold uppercase tracking-wider mb-1">
            <Globe className="w-4 h-4 text-emerald-400" />
            <span>GLOBAL & REGIONAL STRATEGIC INTELLIGENCE</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold font-mono text-slate-100">
            Geopolitical Stress Map & PSX Contagion Radar
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-3xl">
            Curated editorial context on macro stress zones that affect fertilizer sector inputs (gas feedstock, import costs, subsidy policy). Not live intelligence — editorial analysis only.
          </p>
          <span className="inline-flex items-center gap-1.5 mt-1.5 text-[10px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
            Editorial analysis — not live data
          </span>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            <span>Hormuz Oil Shipping Critical</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span>IMF SLA Active</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <div className="lg:col-span-7 bg-[#0b0e16] border border-slate-800/90 rounded-xl p-4 relative min-h-[420px] flex flex-col justify-between overflow-hidden shadow-2xl">

          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

          <div className="relative z-10 flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800">
              COORDINATES: SOUTH ASIA & MIDDLE EAST HUB
            </span>
            <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              RADAR ACTIVE
            </span>
          </div>

          <div className="relative z-10 my-auto py-6">
            <div className="relative w-full aspect-[16/9] bg-[#070a10] border border-slate-800/80 rounded-lg overflow-hidden shadow-inner flex items-center justify-center">

              <svg className="w-full h-full opacity-30 text-slate-600" viewBox="0 0 1000 500" fill="currentColor">
                <path d="M 450 120 Q 520 100 620 120 T 750 150 T 820 220 T 720 280 T 650 320 T 580 250 T 500 200 Z" fill="#1e293b" />
                <path d="M 600 210 Q 640 220 660 260 T 640 340 T 610 320 T 590 250 Z" fill="#334155" />
                <path d="M 500 220 Q 550 230 570 280 T 520 320 T 480 260 Z" fill="#1e293b" />
                <path d="M 420 220 Q 480 250 490 320 T 430 420 T 380 340 T 400 250 Z" fill="#1e293b" />
                <path d="M 120 100 Q 250 80 280 180 T 220 260 T 150 200 Z" fill="#1e293b" />
              </svg>

              <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-emerald-500/30" strokeDasharray="4 4">
                <line x1="58%" y1="48%" x2="65%" y2="54%" stroke="#10b981" strokeWidth="1.5" className="animate-pulse" />
                <line x1="24%" y1="35%" x2="68%" y2="42%" stroke="#f59e0b" strokeWidth="1.5" />
                <line x1="63%" y1="52%" x2="65%" y2="54%" stroke="#3b82f6" strokeWidth="1.5" />
              </svg>

              {hotspots.map((spot) => {
                const isSelected = selectedHotspot?.id === spot.id;
                const isCritical = spot.status === 'CRITICAL';
                const isElevated = spot.status === 'ELEVATED';

                return (
                  <div
                    key={spot.id}
                    onClick={() => setSelectedHotspot(spot)}
                    style={{ left: `${spot.xPct}%`, top: `${spot.yPct}%` }}
                    className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-20"
                  >
                    <span className="relative flex h-6 w-6 items-center justify-center">
                      <span
                        className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                          isCritical
                            ? 'bg-rose-500'
                            : isElevated
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                      ></span>
                      <span
                        className={`relative inline-flex rounded-full h-3.5 w-3.5 border-2 border-slate-900 transition-transform ${
                          isSelected ? 'scale-125 ring-2 ring-white' : 'group-hover:scale-110'
                        } ${
                          isCritical
                            ? 'bg-rose-500'
                            : isElevated
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                      ></span>
                    </span>

                    <div className="absolute left-1/2 -translate-x-1/2 bottom-7 hidden group-hover:flex flex-col items-center pointer-events-none z-30">
                      <div className="bg-[#0f172a] text-slate-100 font-mono text-[10px] py-1 px-2.5 rounded border border-slate-700 whitespace-nowrap shadow-xl">
                        {spot.name}
                      </div>
                      <div className="w-2 h-2 bg-[#0f172a] rotate-45 -mt-1 border-r border-b border-slate-700"></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="relative z-10 flex items-center justify-between pt-3 border-t border-slate-800/80 overflow-x-auto gap-2">
            {hotspots.map((spot) => (
              <button
                key={spot.id}
                onClick={() => setSelectedHotspot(spot)}
                className={`px-2.5 py-1 rounded text-[11px] font-mono whitespace-nowrap transition-all ${
                  selectedHotspot?.id === spot.id
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-bold'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {spot.name.split('&')[0]}
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-5 bg-[#0e131f] border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-xl">
          {selectedHotspot ? (
            <div className="space-y-4">

              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                    SELECTED GEOPOLITICAL HUB
                  </span>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      selectedHotspot.status === 'CRITICAL'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : selectedHotspot.status === 'ELEVATED'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    }`}
                  >
                    STATUS: {selectedHotspot.status}
                  </span>
                </div>

                <h3 className="text-lg font-bold font-mono text-slate-100 mt-1">
                  {selectedHotspot.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {selectedHotspot.summary}
                </p>
              </div>

              <div className="bg-[#141b2a] border border-slate-800 rounded-lg p-3.5 space-y-2">
                <div className="flex items-center space-x-1.5 text-xs font-mono font-semibold text-emerald-400">
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span>DIRECT PSX CONTAGION & TRANSMISSION:</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {selectedHotspot.impactOnPSX}
                </p>
              </div>

              <div>
                <span className="text-[11px] font-mono text-slate-400 block mb-1.5">
                  KEY IMPACTED PSX TICKERS:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedHotspot.affectedTickers.map((ticker) => (
                    <span
                      key={ticker}
                      className="text-xs font-mono font-bold bg-slate-800 hover:bg-slate-700 text-emerald-400 px-2.5 py-1 rounded border border-slate-700 cursor-pointer transition-all"
                    >
                      ${ticker}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono font-semibold text-slate-300">
                    REAL-TIME NEWS AFFECTING THIS HUB ({relatedNews.length})
                  </span>
                  <button
                    onClick={() => onSelectHotspotNewsFilter(selectedHotspot.region)}
                    className="text-[11px] font-mono text-emerald-400 hover:underline flex items-center"
                  >
                    <span>Filter Terminal Feed</span>
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </button>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {relatedNews.length > 0 ? (
                    relatedNews.map((news) => (
                      <div
                        key={news.id}
                        onClick={() => onOpenNewsDetail(news)}
                        className="p-2.5 bg-[#0b0e16] hover:bg-[#121826] border border-slate-800/80 rounded-lg cursor-pointer transition-all space-y-1"
                      >
                        <div className="flex items-center justify-between text-[10px] font-mono">
                          <span
                            className={`font-semibold ${
                              news.sentiment === 'BULLISH'
                                ? 'text-emerald-400'
                                : news.sentiment === 'BEARISH'
                                ? 'text-rose-400'
                                : 'text-slate-400'
                            }`}
                          >
                            {news.sentimentScore > 0 ? `+${news.sentimentScore}` : news.sentimentScore} {news.sentiment}
                          </span>
                          <span className="text-slate-500">{news.publishedAt}</span>
                        </div>
                        <p className="text-xs font-semibold text-slate-200 line-clamp-2">
                          {news.title}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 bg-[#0b0e16] border border-slate-800 rounded-lg text-center text-xs text-slate-500 font-mono">
                      No fertilizer sector announcements matched this hotspot&apos;s tickers.
                    </div>
                  )}
                </div>
              </div>

            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 font-mono text-xs">
              Select a strategic hotspot on the map to inspect PSX contagion mechanisms.
            </div>
          )}

          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="text-amber-400/80">Curated editorial context — not live data</span>
            <button
              onClick={() => onSelectHotspotNewsFilter(selectedHotspot?.region || '')}
              className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center space-x-1"
            >
              <span>View Terminal Stream</span>
              <ExternalLink className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
