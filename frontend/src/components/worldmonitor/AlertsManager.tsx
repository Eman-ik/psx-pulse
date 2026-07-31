"use client";

import React, { useState } from 'react';
import { QuantAlertRule, AlertNotification, NewsCategory, PSXNewsItem } from './types';
import { Bell, ShieldAlert, Plus, Trash2, CheckCircle2, Volume2, VolumeX, AlertTriangle, ArrowRight, Zap } from 'lucide-react';

interface AlertsManagerProps {
  alertRules: QuantAlertRule[];
  onAddRule: (rule: Omit<QuantAlertRule, 'id' | 'createdTime'>) => void;
  onToggleRule: (ruleId: string) => void;
  onDeleteRule: (ruleId: string) => void;
  notifications: AlertNotification[];
  onOpenNewsDetail: (news: PSXNewsItem) => void;
  onClearNotifications: () => void;
}

export const AlertsManager: React.FC<AlertsManagerProps> = ({
  alertRules,
  onAddRule,
  onToggleRule,
  onDeleteRule,
  notifications,
  onOpenNewsDetail,
  onClearNotifications
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [ruleName, setRuleName] = useState('');
  const [ruleCategory, setRuleCategory] = useState<NewsCategory>('ALL');
  const [ruleTicker, setRuleTicker] = useState('');
  const [ruleMinSentiment, setRuleMinSentiment] = useState(50);
  const [ruleMinVolatility, setRuleMinVolatility] = useState(6);
  const [ruleKeyword, setRuleKeyword] = useState('');
  const [ruleAudio, setRuleAudio] = useState(true);

  const handleCreateRuleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleName.trim()) return;

    onAddRule({
      name: ruleName,
      category: ruleCategory,
      tickerFilter: ruleTicker,
      minSentimentScore: Number(ruleMinSentiment),
      minVolatility: Number(ruleMinVolatility),
      keyword: ruleKeyword,
      active: true,
      notifyAudio: ruleAudio
    });

    setRuleName('');
    setRuleTicker('');
    setRuleKeyword('');
    setShowCreateModal(false);
  };

  return (
    <div className="space-y-6 font-mono">

      <div className="bg-[#0e131f] border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Bell className="w-4 h-4 text-emerald-400" />
            <span>QUANT ALERT & NOTIFICATION ENGINE</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-100 font-mono">
            Customizable Quant Alerts & Real-time Trigger Rules
          </h2>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Configure threshold rules based on sentiment scores, volatility indices, stock tickers, or geopolitical keywords. Receive instant live alerts during trading sessions.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded-lg shadow-lg flex items-center space-x-2 shrink-0 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Alert Rule</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <div className="lg:col-span-7 bg-[#0e131f] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              <span>ACTIVE QUANT ALERT RULES ({alertRules.length})</span>
            </h3>
            <span className="text-xs text-slate-400">Status: Monitoring Live Stream</span>
          </div>

          <div className="space-y-3">
            {alertRules.map((rule) => (
              <div
                key={rule.id}
                className={`p-4 rounded-xl border transition-all ${
                  rule.active
                    ? 'bg-[#121826] border-slate-800 hover:border-slate-700'
                    : 'bg-[#090c12] border-slate-900 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-100 text-sm">{rule.name}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          rule.active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-500'
                        }`}
                      >
                        {rule.active ? 'ACTIVE' : 'PAUSED'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-slate-400">
                      <span>Category: <strong className="text-slate-200">{rule.category}</strong></span>
                      {rule.tickerFilter && (
                        <span>• Tickers: <strong className="text-emerald-400">${rule.tickerFilter}</strong></span>
                      )}
                      {rule.minSentimentScore && (
                        <span>• Min Sentiment: <strong className="text-emerald-400">≥ |{rule.minSentimentScore}|</strong></span>
                      )}
                      {rule.minVolatility && (
                        <span>• Volatility: <strong className="text-amber-400">≥ {rule.minVolatility}/10</strong></span>
                      )}
                      {rule.keyword && (
                        <span>• Keywords: <strong className="text-slate-200">{rule.keyword}</strong></span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => onToggleRule(rule.id)}
                      className={`px-3 py-1 text-xs font-bold rounded transition-all ${
                        rule.active
                          ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border border-amber-500/40'
                          : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/40'
                      }`}
                    >
                      {rule.active ? 'Pause' : 'Activate'}
                    </button>

                    <button
                      onClick={() => onDeleteRule(rule.id)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded transition-all"
                      title="Delete Rule"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-5 bg-[#0e131f] border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span>ALERT NOTIFICATIONS LOG ({notifications.length})</span>
              </h3>
              {notifications.length > 0 && (
                <button
                  onClick={onClearNotifications}
                  className="text-xs text-slate-400 hover:text-slate-200 underline"
                >
                  Clear All
                </button>
              )}
            </div>

            <div className="space-y-3 mt-3 max-h-[480px] overflow-y-auto pr-1">
              {notifications.length > 0 ? (
                notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => onOpenNewsDetail(notif.newsItem)}
                    className="p-3 bg-[#121826] hover:bg-[#182033] border border-slate-800 rounded-lg cursor-pointer transition-all space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-rose-400 font-bold bg-rose-950/60 px-2 py-0.5 rounded border border-rose-500/30">
                        ⚡ {notif.ruleName}
                      </span>
                      <span className="text-slate-500">{notif.timestamp}</span>
                    </div>

                    <h4 className="text-xs font-bold text-slate-100 line-clamp-2">
                      {notif.newsItem.title}
                    </h4>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                      <span>Sentiment: <strong className="text-emerald-400">{notif.newsItem.sentimentScore} {notif.newsItem.sentiment}</strong></span>
                      <span className="text-emerald-400 flex items-center font-bold">
                        Inspect <ArrowRight className="w-3 h-3 ml-0.5" />
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-slate-500 font-mono space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
                  <p>No new alert triggers logged during this session.</p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400">
            Rules evaluate live against incoming web scraper items and AI sentiment scores.
          </div>
        </div>

      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0e131f] border border-slate-800 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">
                Create Customizable Quant Alert Rule
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRuleSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Alert Rule Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Banking Sector Rate Cut Shock"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category Filter</label>
                  <select
                    value={ruleCategory}
                    onChange={(e) => setRuleCategory(e.target.value as NewsCategory)}
                    className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="ALL">All Categories</option>
                    <option value="PSX_EQUITIES">PSX Equities</option>
                    <option value="GEOPOLITICS">Geopolitics</option>
                    <option value="MACRO_SBP_IMF">Macro / SBP / IMF</option>
                    <option value="COMMODITIES_FX">Commodities & FX</option>
                    <option value="QUANT_SIGNALS">Quant Signals</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Target Stock Tickers</label>
                  <input
                    type="text"
                    placeholder="OGDC, PPL, SYS"
                    value={ruleTicker}
                    onChange={(e) => setRuleTicker(e.target.value)}
                    className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Min Absolute Sentiment Score (|Score| ≥ {ruleMinSentiment})
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={ruleMinSentiment}
                    onChange={(e) => setRuleMinSentiment(Number(e.target.value))}
                    className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Min Volatility Score (≥ {ruleMinVolatility}/10)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={ruleMinVolatility}
                    onChange={(e) => setRuleMinVolatility(Number(e.target.value))}
                    className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Keyword Filter</label>
                <input
                  type="text"
                  placeholder="Oil, Rate Cut, Tranche, Tariff"
                  value={ruleKeyword}
                  onChange={(e) => setRuleKeyword(e.target.value)}
                  className="w-full bg-[#141a26] border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="notifyAudio"
                  checked={ruleAudio}
                  onChange={(e) => setRuleAudio(e.target.checked)}
                  className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500"
                />
                <label htmlFor="notifyAudio" className="text-slate-300 cursor-pointer">
                  Enable Audio Beep on Rule Trigger
                </label>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold shadow-lg"
                >
                  Save Alert Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
