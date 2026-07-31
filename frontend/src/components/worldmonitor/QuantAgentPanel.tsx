"use client";

import React, { useState, useRef, useEffect } from 'react';
import { AgentChatMessage } from './types';
import { Bot, Send, User, Sparkles, RefreshCw, ExternalLink, ShieldAlert, Copy, Check, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';

interface QuantAgentPanelProps {
  messages: AgentChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
  isGenerating: boolean;
}

export const QuantAgentPanel: React.FC<QuantAgentPanelProps> = ({
  messages,
  onSendMessage,
  isGenerating
}) => {
  const [inputText, setInputText] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const PRESET_PROMPTS = [
    "How does a 100 bps SBP rate cut impact Cement ($LUCK, $DGKC) vs Banking ($MCB, $UBL)?",
    "Analyze Brent Crude spike to $76.8/bbl on OGDC, PPL, and ATRL revenue and EPS.",
    "What is the quantitative 30-day outlook for Systems Limited ($SYS) IT exports?",
    "Evaluate IMF $1.1B tranche conditions on Circular Debt resolution for $HUBC and $KEL."
  ];

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isGenerating) return;
    const text = inputText;
    setInputText('');
    await onSendMessage(text);
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="bg-[#0e131f] border border-slate-800 rounded-xl flex flex-col h-[750px] shadow-2xl overflow-hidden">

      <div className="p-4 bg-[#0b0e16] border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-mono shadow-[0_0_12px_rgba(16,185,129,0.2)]">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-bold font-mono text-slate-100 text-sm sm:text-base">PSX QuantAgent v3.6</h3>
              <span className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
                GROUNDED SEARCH ENGINE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Autonomous Macroeconomic, Geopolitical & PSX Equity AI Research Engine
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>GEMINI-3.6-FLASH SEARCH READY</span>
        </div>
      </div>

      <div className="p-3 bg-[#121826] border-b border-slate-800/80 overflow-x-auto">
        <div className="flex items-center space-x-2 min-w-max">
          <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold shrink-0 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            <span>QUANT PROMPTS:</span>
          </span>
          {PRESET_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => onSendMessage(prompt)}
              disabled={isGenerating}
              className="px-2.5 py-1 bg-[#182030] hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/70 rounded text-xs font-mono transition-all truncate max-w-xs"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#0a0d14] font-sans">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-mono font-bold ${
                  isUser
                    ? 'bg-slate-800 text-slate-200 border border-slate-700'
                    : 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-xl p-4 space-y-3 shadow-md ${
                  isUser
                    ? 'bg-emerald-600 text-white font-medium text-xs sm:text-sm'
                    : 'bg-[#0f1522] border border-slate-800 text-slate-200 text-xs sm:text-sm leading-relaxed'
                }`}
              >
                <div className="whitespace-pre-wrap font-sans space-y-2">{msg.text}</div>

                {!isUser && msg.impactData && msg.impactData.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-1.5 font-mono">
                    <span className="text-[10px] uppercase text-emerald-400 font-bold block">
                      ⚡ PROJECTED TICKER TRANSMISSION IMPACTS:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {msg.impactData.map((item, idx) => (
                        <div key={idx} className="p-2 bg-[#080b12] border border-slate-800 rounded flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-1.5">
                            <span className="font-bold text-slate-100">${item.ticker}</span>
                            <span className="text-[10px] text-slate-400">({item.horizon})</span>
                          </div>
                          <span
                            className={`font-bold flex items-center ${
                              item.direction === 'up'
                                ? 'text-emerald-400'
                                : item.direction === 'down'
                                ? 'text-rose-400'
                                : 'text-slate-400'
                            }`}
                          >
                            {item.direction === 'up' && <TrendingUp className="w-3 h-3 mr-0.5" />}
                            {item.direction === 'down' && <TrendingDown className="w-3 h-3 mr-0.5" />}
                            {item.percentage}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {!isUser && msg.groundingSources && msg.groundingSources.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-1 font-mono text-[11px]">
                    <span className="text-slate-400 block font-semibold">GROUNDED SOURCES:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.groundingSources.slice(0, 4).map((src, idx) => (
                        <a
                          key={idx}
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 px-2 py-0.5 bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-slate-800 rounded truncate max-w-[200px]"
                        >
                          <ExternalLink className="w-3 h-3 shrink-0" />
                          <span className="truncate">{src.title || src.url}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {!isUser && (
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                    <span>{msg.timestamp}</span>
                    <button
                      onClick={() => handleCopy(msg.id, msg.text)}
                      className="flex items-center space-x-1 text-slate-400 hover:text-slate-200"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Response</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isGenerating && (
          <div className="flex items-center space-x-3 text-slate-400 font-mono text-xs">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
            </div>
            <div className="p-3 bg-[#0f1522] border border-slate-800 rounded-lg space-y-1">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                <span>Running grounded Gemini-3.6 search and quant models...</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Scanning PSX market disclosures, SBP MPS data, and global commodity transmissions.
              </p>
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-3 bg-[#0b0e16] border-t border-slate-800 flex items-center gap-2">
        <input
          type="text"
          placeholder="Ask PSX QuantAgent about stocks, interest rates, commodities, or geopolitics..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={isGenerating}
          className="flex-1 bg-[#141a26] border border-slate-700 rounded-lg px-4 py-2 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isGenerating}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-mono text-xs font-bold rounded-lg shadow-lg flex items-center space-x-1.5 shrink-0 transition-all"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>

    </div>
  );
};
