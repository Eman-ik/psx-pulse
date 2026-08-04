"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { MacroTickerBanner } from './MacroTickerBanner';
import { LiveNewsTerminal } from './LiveNewsTerminal';
import { WorldGeopoliticalMap } from './WorldGeopoliticalMap';
import { QuantAgentPanel } from './QuantAgentPanel';
import { HistoricalAnalytics } from './HistoricalAnalytics';
import { AlertsManager } from './AlertsManager';
import { MarketHeatmap } from './MarketHeatmap';
import { CompanyDisclosuresTerminal } from './CompanyDisclosuresTerminal';
import { NewsTab } from './NewsTab';
import { EquityResearchTab } from './EquityResearchTab';
import { NewsDetailModal } from './NewsDetailModal';
import { ExportReportModal } from './ExportReportModal';
import type { NewsAnnouncement, LiveQuote, ComparisonRow } from '@/lib/api';

import {
  PSXNewsItem,
  MacroIndicator,
  SectorSentiment,
  QuantAlertRule,
  AlertNotification,
  AgentChatMessage,
  NewsCategory,
  SentimentType,
  ImpactHorizon,
} from './types';

interface WorldMonitorTerminalProps {
  realAnnouncements?: NewsAnnouncement[];
  companyById?: Record<number, { name: string; symbol: string | null }>;
  liveQuotes?: LiveQuote[];
  comparison?: ComparisonRow[];
}

import {
  INITIAL_MACRO_INDICATORS,
  MAP_HOTSPOTS,
  INITIAL_SECTOR_SENTIMENT,
  INITIAL_ALERT_RULES
} from './data/mockAndInitialData';

import {
  BarChart2,
  Globe,
  Cpu,
  TrendingUp,
  Bell,
  Grid,
  FileText,
  Radio,
  Download,
  Newspaper,
  FileSearch,
} from 'lucide-react';

// Convert a real DB announcement to the PSXNewsItem shape used by LiveNewsTerminal.
// Fields that require AI analysis (trendProjection, aiAnalysis) are intentionally
// left absent — they are optional in the type and conditionally rendered in the UI.
function convertAnnouncementToNewsItem(
  a: NewsAnnouncement,
  companyById: Record<number, { name: string; symbol: string | null }>
): PSXNewsItem {
  const company = a.issuer_id != null ? companyById[a.issuer_id] : null;
  const ticker = company?.symbol ?? null;
  const score = a.sentiment_score ?? 0;
  const sentiment: SentimentType =
    score > 0.2 ? 'BULLISH' : score < -0.2 ? 'BEARISH' : 'NEUTRAL';

  const categoryMap: Record<string, NewsCategory> = {
    payout: 'PSX_EQUITIES',
    results: 'PSX_EQUITIES',
    leadership: 'PSX_EQUITIES',
    regulatory: 'PSX_EQUITIES',
    operations: 'PSX_EQUITIES',
    general: 'PSX_EQUITIES',
  };

  const horizonMap: Record<string, ImpactHorizon> = {
    payout: '1-MONTH',
    results: '3-MONTHS',
    leadership: '1-MONTH',
    regulatory: '1-WEEK',
    operations: '1-MONTH',
    general: '1-WEEK',
  };

  const volatilityMap: Record<string, number> = {
    results: 7,
    payout: 6,
    leadership: 4,
    regulatory: 5,
    operations: 5,
    general: 3,
  };

  // Format published_at as "YYYY-MM-DD"
  const publishedAt = a.published_at.slice(0, 10);

  return {
    id: `db-${a.id}`,
    title: a.title,
    summary: a.summary ?? 'Official corporate announcement filed with PSX.',
    source: 'PSX Official Announcements',
    publishedAt,
    category: categoryMap[a.category] ?? 'PSX_EQUITIES',
    tickers: ticker ? [ticker] : [],
    sentiment,
    sentimentScore: Math.round(Math.abs(score) * 100),
    volatilityScore: volatilityMap[a.category] ?? 4,
    impactHorizon: horizonMap[a.category] ?? '1-WEEK',
    url: a.source_url ?? undefined,
  };
}

export default function WorldMonitorTerminal({
  realAnnouncements = [],
  companyById = {},
  liveQuotes = [],
  comparison = [],
}: WorldMonitorTerminalProps) {
  const [activeTab, setActiveTab] = useState<'news' | 'equity' | 'stream' | 'map' | 'agent' | 'analytics' | 'alerts' | 'heatmap' | 'disclosures'>('news');

  const [macroIndicators, setMacroIndicators] = useState<MacroIndicator[]>(INITIAL_MACRO_INDICATORS);
  const [hotspots] = useState(MAP_HOTSPOTS);
  const [sectorSentiment] = useState<SectorSentiment[]>(INITIAL_SECTOR_SENTIMENT);
  const [alertRules, setAlertRules] = useState<QuantAlertRule[]>(INITIAL_ALERT_RULES);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);

  // Real announcements converted for the Live Stream
  const realNewsItems: PSXNewsItem[] = React.useMemo(
    () => realAnnouncements.map((a) => convertAnnouncementToNewsItem(a, companyById)),
    [realAnnouncements, companyById]
  );

  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<SentimentType | 'ALL'>('ALL');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [selectedNewsDetail, setSelectedNewsDetail] = useState<PSXNewsItem | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const [isGeneratingAgentReply, setIsGeneratingAgentReply] = useState(false);

  const [chatMessages, setChatMessages] = useState<AgentChatMessage[]>([
    {
      id: 'welcome-msg',
      sender: 'agent',
      text: `Welcome to **PSX QuantAgent** — your fertilizer sector research terminal.

I am grounded in live data for the PSX fertilizer pilot: **FFC, EFERT, FATIMA, AGL, AHCL**.

I can answer questions about:
- Company fundamentals, ratios, and financial results
- Dividend history and payout analysis
- Macro drivers: SBP policy rate, CPI, PKR/USD, urea pricing
- Sector comparison and peer benchmarking

Ask me anything about these companies or the fertilizer sector.`,
      timestamp: 'System Boot'
    }
  ]);

  // Fetch real macro data on mount and replace initial mock values
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

    Promise.all([
      fetch(`${apiBase}/market/index/KSE100/prices`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${apiBase}/macro/live-snapshot`).then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([kse, macro]) => {
      setMacroIndicators(prev => prev.map(ind => {

        if (ind.id === 'kse100' && kse?.bars?.length) {
          const bars: { date: string; close: number }[] = kse.bars;
          const lat = bars[bars.length - 1];
          const pre = bars.length >= 2 ? bars[bars.length - 2] : null;
          const chg = pre ? lat.close - pre.close : 0;
          const chgPct = pre ? (chg / pre.close) * 100 : 0;
          // Use last 7 real closes for sparkline
          const sparkline = bars.slice(-7).map(b => b.close);
          return {
            ...ind,
            value: lat.close.toLocaleString(undefined, { maximumFractionDigits: 1 }),
            change: `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}`,
            changePercent: chgPct,
            status: chgPct > 0 ? 'up' : chgPct < 0 ? 'down' : 'flat',
            lastUpdated: `EOD ${lat.date}`,
            sparkline,
          };
        }

        if (!macro) return ind;

        if (ind.id === 'pkr_usd' && macro.pkr_usd) {
          const val: number = macro.pkr_usd.value;
          const prevVal: number | null = macro.pkr_usd_monthly?.prev_value ?? null;
          const chg = prevVal != null ? val - prevVal : null;
          return {
            ...ind,
            value: val.toFixed(2),
            ...(chg != null && prevVal != null ? {
              change: `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}`,
              changePercent: (chg / prevVal) * 100,
              status: (chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat') as 'up' | 'down' | 'flat',
            } : {}),
            lastUpdated: macro.pkr_usd.source as string,
          };
        }

        if (ind.id === 'brent_crude' && macro.brent_crude) {
          const val: number = macro.brent_crude.value;
          const prev: number = macro.brent_crude.prev_close;
          const chg = val - prev;
          const chgPct = prev !== 0 ? (chg / prev) * 100 : 0;
          return {
            ...ind,
            value: `$${val.toFixed(2)}`,
            change: `${chg >= 0 ? '+' : ''}$${Math.abs(chg).toFixed(2)}`,
            changePercent: chgPct,
            status: chgPct > 0 ? 'up' : chgPct < 0 ? 'down' : 'flat',
            lastUpdated: macro.brent_crude.source as string,
          };
        }

        if (ind.id === 'sbp_rate' && macro.sbp_rate) {
          const val: number = macro.sbp_rate.value;
          const prevVal: number | null = macro.sbp_rate.prev_value ?? null;
          const chg = prevVal != null ? val - prevVal : null;
          return {
            ...ind,
            value: `${val.toFixed(2)}%`,
            ...(chg != null ? {
              change: `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`,
              changePercent: chg,
              status: (chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat') as 'up' | 'down' | 'flat',
            } : {}),
            lastUpdated: `SBP · ${(macro.sbp_rate.period as string).slice(0, 7)}`,
          };
        }

        if (ind.id === 'cpi_inflation') {
          const cpi = macro.cpi_monthly ?? macro.cpi_wb;
          if (cpi) {
            const val: number = cpi.value;
            const prevVal: number | null = cpi.prev_value ?? null;
            const chg = prevVal != null ? val - prevVal : null;
            const label = macro.cpi_monthly
              ? `SBP/PBS · ${(macro.cpi_monthly.period as string).slice(0, 7)}`
              : `World Bank (annual · ${macro.cpi_wb.period})`;
            return {
              ...ind,
              value: `${val.toFixed(2)}%`,
              ...(chg != null ? {
                change: `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`,
                changePercent: chg,
                status: (chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat') as 'up' | 'down' | 'flat',
              } : {}),
              lastUpdated: label,
            };
          }
        }

        if (ind.id === 'fx_reserves' && macro.fx_reserves) {
          const valMn: number = macro.fx_reserves.value;
          const prevMn: number | null = macro.fx_reserves.prev_value ?? null;
          const chgMn = prevMn != null ? valMn - prevMn : null;
          return {
            ...ind,
            value: `$${(valMn / 1000).toFixed(2)} B`,
            ...(chgMn != null && prevMn != null ? {
              change: `${chgMn >= 0 ? '+' : ''}$${Math.round(Math.abs(chgMn))} M`,
              changePercent: (chgMn / prevMn) * 100,
              status: (chgMn > 0 ? 'up' : chgMn < 0 ? 'down' : 'flat') as 'up' | 'down' | 'flat',
            } : {}),
            lastUpdated: `SBP · ${(macro.fx_reserves.period as string).slice(0, 7)}`,
          };
        }

        return ind;
      }));
    });
  }, []);

  const evaluateAlertRules = useCallback((itemsToEvaluate: PSXNewsItem[], currentRules: QuantAlertRule[]) => {
    const newAlerts: AlertNotification[] = [];
    currentRules.filter(r => r.active).forEach(rule => {
      itemsToEvaluate.forEach(item => {
        if (rule.category !== 'ALL' && item.category !== rule.category) return;
        if (rule.tickerFilter) {
          const ruleTickers = rule.tickerFilter.split(',').map(t => t.trim().toUpperCase());
          if (!item.tickers.some(t => ruleTickers.includes(t.toUpperCase()))) return;
        }
        if (rule.minSentimentScore && Math.abs(item.sentimentScore) < rule.minSentimentScore) return;
        if (rule.minVolatility && item.volatilityScore < rule.minVolatility) return;
        if (rule.keyword) {
          const kwList = rule.keyword.split(',').map(k => k.trim().toLowerCase());
          const itemText = (item.title + ' ' + item.summary).toLowerCase();
          if (!kwList.some(kw => itemText.includes(kw))) return;
        }
        newAlerts.push({
          id: `alert-${rule.id}-${item.id}-${Date.now()}`,
          ruleId: rule.id,
          ruleName: rule.name,
          newsItem: item,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          read: false
        });
      });
    });
    if (newAlerts.length > 0) setNotifications(prev => [...newAlerts, ...prev]);
  }, []);

  // Run alert rules against real news on mount
  useEffect(() => {
    if (realNewsItems.length > 0) evaluateAlertRules(realNewsItems, alertRules);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [realNewsItems]);

  const handleSendMessage = async (userPromptText: string) => {
    if (!userPromptText.trim() || isGeneratingAgentReply) return;

    const userMsg: AgentChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userPromptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMsg]);
    setIsGeneratingAgentReply(true);

    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userPromptText,
          chatHistory: chatMessages.slice(-6).map(m => ({
            role: m.sender === 'user' ? 'user' : 'assistant',
            content: m.text
          }))
        })
      });

      const data = await response.json();

      if (response.ok && data.reply) {
        setChatMessages(prev => [...prev, {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          text: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          groundingSources: data.groundingSources,
        }]);
      } else {
        const errText = data.error || (response.status === 503
          ? 'ANTHROPIC_API_KEY is not configured. Add it to frontend/.env.local to enable the AI agent.'
          : `Request failed (${response.status})`);
        setChatMessages(prev => [...prev, {
          id: `err-${Date.now()}`,
          sender: 'agent',
          text: `⚠️ **QuantAgent unavailable**: ${errText}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Network error';
      setChatMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        sender: 'agent',
        text: `⚠️ **QuantAgent unavailable**: ${msg}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsGeneratingAgentReply(false);
    }
  };

  const handleSelectHotspotNewsFilter = (ticker: string) => {
    setSelectedTicker(ticker);
    setActiveTab('stream');
  };

  const handleAddRule = (ruleData: Omit<QuantAlertRule, 'id' | 'createdTime'>) => {
    setAlertRules(prev => [...prev, {
      ...ruleData,
      id: `rule-${Date.now()}`,
      createdTime: new Date().toLocaleDateString()
    }]);
  };

  const handleToggleRule = (id: string) => {
    setAlertRules(prev => prev.map(r => r.id === id ? { ...r, active: !r.active } : r));
  };

  const handleDeleteRule = (id: string) => {
    setAlertRules(prev => prev.filter(r => r.id !== id));
  };

  const unreadAlertsCount = notifications.filter(n => !n.read).length;

  const tabs = [
    { id: 'news' as const, label: 'News', icon: <Newspaper className="w-4 h-4" /> },
    { id: 'equity' as const, label: 'Equity Research', icon: <FileSearch className="w-4 h-4" /> },
    { id: 'stream' as const, label: 'Announcements', icon: <Radio className="w-4 h-4" /> },
    { id: 'heatmap' as const, label: 'Market Heatmap', icon: <Grid className="w-4 h-4" /> },
    { id: 'map' as const, label: 'Macro Context', icon: <Globe className="w-4 h-4" /> },
    { id: 'agent' as const, label: 'QuantAgent AI', icon: <Cpu className="w-4 h-4" /> },
    { id: 'analytics' as const, label: 'Analytics', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'alerts' as const, label: 'Alerts', icon: <Bell className="w-4 h-4" />, badge: unreadAlertsCount },
    { id: 'disclosures' as const, label: 'PSX Disclosures', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <div className="bg-[#09090b] text-[#fafafa] font-mono selection:bg-[#3b82f6] selection:text-white">

      <div className="bg-[#0d0d0f] border-b border-[#27272a] sticky top-0 z-40">
        <div className="px-4 py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></div>
              <span className="text-xs font-bold text-[#10b981] uppercase tracking-widest">PSX WorldMonitor</span>
            </div>
            <span className="text-[#3f3f46] hidden sm:inline">|</span>
            <span className="text-[10px] text-[#71717a] hidden sm:inline">Fertilizer Sector Research Terminal · {realAnnouncements.length} real announcements</span>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:flex-none sm:w-56">
              <input
                type="text"
                placeholder="Search FFC, EFERT, FATIMA..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#18181b] border border-[#27272a] rounded px-3 py-1.5 text-[11px] text-[#fafafa] placeholder-[#52525b] focus:outline-none focus:border-[#3b82f6]"
              />
            </div>
            <button
              onClick={() => setIsExportModalOpen(true)}
              className="px-3 py-1.5 bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] text-[#a1a1aa] hover:text-[#fafafa] rounded text-[11px] font-bold flex items-center space-x-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-1 px-4 overflow-x-auto pb-px">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-1.5 px-3 py-2 text-[11px] font-bold border-b-2 transition-all whitespace-nowrap relative ${
                activeTab === tab.id
                  ? 'border-[#3b82f6] text-[#3b82f6]'
                  : 'border-transparent text-[#71717a] hover:text-[#a1a1aa]'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge != null && tab.badge > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#ef4444] text-white text-[9px] rounded-full flex items-center justify-center font-black">
                  {tab.badge > 9 ? '9+' : tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <MacroTickerBanner indicators={macroIndicators} />

      {activeTab === 'news' && (
        <NewsTab
          announcements={realAnnouncements}
          companyById={companyById}
        />
      )}

      {activeTab === 'equity' && <EquityResearchTab />}

      <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 ${activeTab === 'news' || activeTab === 'equity' ? 'hidden' : ''}`}>

        {activeTab === 'stream' && (
          <LiveNewsTerminal
            newsItems={realNewsItems}
            selectedCategory={selectedCategory}
            setSelectedCategory={setSelectedCategory}
            selectedSentiment={selectedSentiment}
            setSelectedSentiment={setSelectedSentiment}
            selectedTicker={selectedTicker}
            setSelectedTicker={setSelectedTicker}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onOpenNewsDetail={(news) => setSelectedNewsDetail(news)}
            onAskAgent={(promptText) => {
              setActiveTab('agent');
              handleSendMessage(promptText);
            }}
          />
        )}

        {activeTab === 'heatmap' && (
          <MarketHeatmap
            liveQuotes={liveQuotes}
            comparison={comparison}
            companyById={companyById}
            onAskAgent={(promptText) => {
              setActiveTab('agent');
              handleSendMessage(promptText);
            }}
          />
        )}

        {activeTab === 'map' && (
          <WorldGeopoliticalMap
            hotspots={hotspots}
            newsItems={realNewsItems}
            onSelectHotspotNewsFilter={handleSelectHotspotNewsFilter}
            onOpenNewsDetail={(news) => setSelectedNewsDetail(news)}
          />
        )}

        {activeTab === 'agent' && (
          <QuantAgentPanel
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            isGenerating={isGeneratingAgentReply}
          />
        )}

        {activeTab === 'analytics' && (
          <HistoricalAnalytics
            sectorSentiment={sectorSentiment}
            realAnnouncements={realAnnouncements}
            companyById={companyById}
            onAskAgent={(promptText) => {
              setActiveTab('agent');
              handleSendMessage(promptText);
            }}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsManager
            alertRules={alertRules}
            onAddRule={handleAddRule}
            onToggleRule={handleToggleRule}
            onDeleteRule={handleDeleteRule}
            notifications={notifications}
            onOpenNewsDetail={(news) => setSelectedNewsDetail(news)}
            onClearNotifications={() => setNotifications([])}
          />
        )}

        {activeTab === 'disclosures' && (
          <CompanyDisclosuresTerminal
            realAnnouncements={realAnnouncements}
            companyById={companyById}
            onAskAgent={(promptText) => {
              setActiveTab('agent');
              handleSendMessage(promptText);
            }}
          />
        )}

      </div>

      <NewsDetailModal
        news={selectedNewsDetail}
        onClose={() => setSelectedNewsDetail(null)}
        onAskAgent={(promptText) => {
          setSelectedNewsDetail(null);
          setActiveTab('agent');
          handleSendMessage(promptText);
        }}
      />

      <ExportReportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        newsItems={realNewsItems}
        macroIndicators={macroIndicators}
        sectorSentiment={sectorSentiment}
      />

    </div>
  );
}
