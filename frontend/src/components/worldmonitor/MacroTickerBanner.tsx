"use client";

import React from 'react';
import { MacroIndicator } from './types';
import { ArrowUpRight, ArrowDownRight, Minus, Activity } from 'lucide-react';

interface MacroTickerBannerProps {
  indicators: MacroIndicator[];
  onSelectIndicator?: (indicator: MacroIndicator) => void;
}

export const MacroTickerBanner: React.FC<MacroTickerBannerProps> = ({
  indicators,
  onSelectIndicator
}) => {
  return (
    <div className="bg-[#09090b] border-b border-[#27272a] py-2 overflow-x-auto scrollbar-thin scrollbar-thumb-zinc-800">
      <div className="max-w-7xl mx-auto px-4 flex items-center space-x-4 min-w-max">

        <div className="flex items-center space-x-1.5 text-[11px] font-mono font-semibold text-[#3b82f6] bg-[#3b82f6]/10 border border-[#3b82f6]/30 px-2 py-1 rounded shrink-0">
          <Activity className="w-3.5 h-3.5 animate-pulse text-[#3b82f6]" />
          <span>LIVE MACRO & FX:</span>
        </div>

        <div className="flex items-center space-x-2.5">
          {indicators.map((ind) => {
            const isUp = ind.status === 'up';
            const isDown = ind.status === 'down';

            return (
              <div
                key={ind.id}
                onClick={() => onSelectIndicator && onSelectIndicator(ind)}
                className="group cursor-pointer flex items-center space-x-2.5 px-3 py-1.5 bg-[#121214] hover:bg-[#18181b] border border-[#27272a] hover:border-[#3f3f46] rounded-md transition-all shadow-xs"
              >
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[11px] font-mono font-semibold text-[#a1a1aa] group-hover:text-[#fafafa]">
                      {ind.name}
                    </span>
                    {ind.tickerSymbol && (
                      <span className="text-[9px] font-mono text-[#a1a1aa] bg-[#27272a] px-1 rounded">
                        {ind.tickerSymbol}
                      </span>
                    )}
                  </div>

                  <div className="flex items-baseline space-x-2 mt-0.5">
                    <span className="text-xs font-mono font-bold text-[#fafafa]">
                      {ind.value}
                    </span>

                    <div
                      className={`flex items-center text-[10px] font-mono font-semibold px-1 rounded ${
                        isUp
                          ? 'text-[#10b981] bg-[#10b981]/10 border border-[#10b981]/20'
                          : isDown
                          ? 'text-[#ef4444] bg-[#ef4444]/10 border border-[#ef4444]/20'
                          : 'text-[#a1a1aa] bg-[#27272a]'
                      }`}
                    >
                      {isUp && <ArrowUpRight className="w-3 h-3 mr-0.5" />}
                      {isDown && <ArrowDownRight className="w-3 h-3 mr-0.5" />}
                      {!isUp && !isDown && <Minus className="w-3 h-3 mr-0.5" />}
                      <span>{ind.change}</span>
                    </div>
                  </div>
                </div>

                {ind.sparkline && ind.sparkline.length > 1 && (
                  <div className="w-10 h-5 shrink-0 opacity-75 group-hover:opacity-100">
                    <svg className="w-full h-full" viewBox="0 0 40 20">
                      {(() => {
                        const min = Math.min(...ind.sparkline);
                        const max = Math.max(...ind.sparkline) || min + 1;
                        const points = ind.sparkline
                          .map((val, idx) => {
                            const x = (idx / (ind.sparkline.length - 1)) * 38 + 1;
                            const y = 19 - ((val - min) / (max - min)) * 18;
                            return `${x},${y}`;
                          })
                          .join(' ');
                        return (
                          <polyline
                            fill="none"
                            stroke={isUp ? '#10b981' : isDown ? '#ef4444' : '#a1a1aa'}
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            points={points}
                          />
                        );
                      })()}
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};
