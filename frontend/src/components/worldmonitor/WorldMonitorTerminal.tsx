"use client";

import React, { useState, useCallback } from 'react';
import { MacroTickerBanner } from './MacroTickerBanner';
import { LiveNewsTerminal } from './LiveNewsTerminal';
import { WorldGeopoliticalMap } from './WorldGeopoliticalMap';
import { QuantAgentPanel } from './QuantAgentPanel';
import { HistoricalAnalytics } from './HistoricalAnalytics';
import { AlertsManager } from './AlertsManager';
import { MarketHeatmap } from './MarketHeatmap';
import { CompanyDisclosuresTerminal } from './CompanyDisclosuresTerminal';
import { NewsDetailModal } from './NewsDetailModal';
import { ExportReportModal } from './ExportReportModal';

import {
  PSXNewsItem,
  MacroIndicator,
  SectorSentiment,
  QuantAlertRule,
  AlertNotification,
  AgentChatMessage,
  NewsCategory,
  SentimentType,
} from './types';

import {
  INITIAL_MACRO_INDICATORS,
  MAP_HOTSPOTS,
  INITIAL_NEWS_ITEMS,
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
  Scan,
  Loader2
} from 'lucide-react';

export default function WorldMonitorTerminal() {
  const [activeTab, setActiveTab] = useState<'stream' | 'map' | 'agent' | 'analytics' | 'alerts' | 'heatmap' | 'disclosures'>('stream');

  const [macroIndicators, setMacroIndicators] = useState<MacroIndicator[]>(INITIAL_MACRO_INDICATORS);
  const [hotspots, setHotspots] = useState(MAP_HOTSPOTS);
  const [newsItems, setNewsItems] = useState<PSXNewsItem[]>(INITIAL_NEWS_ITEMS);
  const [sectorSentiment, setSectorSentiment] = useState<SectorSentiment[]>(INITIAL_SECTOR_SENTIMENT);
  const [alertRules, setAlertRules] = useState<QuantAlertRule[]>(INITIAL_ALERT_RULES);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);

  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<SentimentType | 'ALL'>('ALL');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [selectedNewsDetail, setSelectedNewsDetail] = useState<PSXNewsItem | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const [isScanningWeb, setIsScanningWeb] = useState(false);
  const [isGeneratingAgentReply, setIsGeneratingAgentReply] = useState(false);

  const [chatMessages, setChatMessages] = useState<AgentChatMessage[]>([
    {
      id: 'welcome-msg',
      sender: 'agent',
      text: `Welcome to **PSX QuantAgent v3.6** terminal.

I am your real-time macroeconomic, geopolitical, and Pakistan Stock Exchange equity research engine. I track:
- **PSX Equities**: $OGDC, $PPL, $SYS, $LUCK, $MCB, $HUBC, $ENGRO, $FFC
- **Macro Drivers**: SBP Policy Rate cuts, CPI inflation, PKR/USD interbank, SBP FX reserves
- **Geopolitics & Commodities**: Middle East oil shipping, Brent Crude, IMF EFF tranches, CPEC energy debt

Ask me any quantitative question or select a preset prompt above to begin.`,
      timestamp: 'System Boot'
    }
  ]);

  const evaluateAlertRules = useCallback((itemsToEvaluate: PSXNewsItem[], currentRules: QuantAlertRule[]) => {
    const newAlerts: AlertNotification[] = [];

    currentRules.filter(r => r.active).forEach(rule => {
      itemsToEvaluate.forEach(item => {
        if (rule.category !== 'ALL' && item.category !== rule.category) return;

        if (rule.tickerFilter) {
          const ruleTickers = rule.tickerFilter.split(',').map(t => t.trim().toUpperCase());
          const matchTicker = item.tickers.some(t => ruleTickers.includes(t.toUpperCase()));
          if (!matchTicker) return;
        }

        if (rule.minSentimentScore && Math.abs(item.sentimentScore) < rule.minSentimentScore) return;
        if (rule.minVolatility && item.volatilityScore < rule.minVolatility) return;

        if (rule.keyword) {
          const kwList = rule.keyword.split(',').map(k => k.trim().toLowerCase());
          const itemText = (item.title + ' ' + item.summary).toLowerCase();
          const matchKw = kwList.some(kw => itemText.includes(kw));
          if (!matchKw) return;
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

    if (newAlerts.length > 0) {
      setNotifications(prev => [...newAlerts, ...prev]);
    }
  }, []);

  const handleTriggerScan = async () => {
    if (isScanningWeb) return;
    setIsScanningWeb(true);

    try {
      const response = await fetch('/api/news/scan-web', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topicFilter: selectedCategory,
          customKeywords: searchQuery
        })
      });

      const data = await response.json();

      if (data.success && Array.isArray(data.items) && data.items.length > 0) {
        setNewsItems(prev => {
          evaluateAlertRules(data.items, alertRules);
          return [...data.items, ...prev];
        });
      }
    } catch (err) {
      console.error('Error during web scan:', err);
    } finally {
      setIsScanningWeb(false);
    }
  };

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
            role: m.sender === 'user' ? 'user' : 'model',
            text: m.text
          }))
        })
      });

      const data = await response.json();

      if (data.success && data.reply) {
        const agentMsg: AgentChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          text: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          groundingSources: data.groundingSources,
          impactData: data.impactData,
          suggestedActions: data.suggestedActions
        };
        setChatMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (err: any) {
      const errorMsg: AgentChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'agent',
        text: `⚠️ **QuantAgent Service Advisory**: Unable to process request due to network connection or API response limits (${err.message || 'Error'}). Please try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsGeneratingAgentReply(false);
    }
  };

  const handleSelectHotspotNewsFilter = (ticker: string) => {
    setSelectedTicker(ticker);
    setActiveTab('stream');
  };

  const handleAddRule = (ruleData: Omit<QuantAlertRule, 'id' | 'createdTime'>) => {
    const newRule: QuantAlertRule = {
      ...ruleData,
      id: `rule-${Date.now()}`,
      createdTime: new Date().toLocaleDateString()
    };
    setAlertRules(prev => [...prev, newRule]);
  };

  const handleToggleRule = (id: string) => {
    setAlertRules(prev => prev.map(r => r.id === id ? { ...r, active: !r.active } : r));
  };

  const handleDeleteRule = (id: string) => {
    setAlertRules(prev => prev.filter(r => r.id !== id));
  };

  const unreadAlertsCount = notifications.filter(n => !n.read).length;

  const tabs = [
    { id: 'stream' as const, label: 'Live Stream', icon: <Radio className="w-4 h-4" /> },
    { id: 'heatmap' as const, label: 'Market Heatmap', icon: <Grid className="w-4 h-4" /> },
    { id: 'map' as const, label: 'Geopolitical Map', icon: <Globe className="w-4 h-4" /> },
    { id: 'agent' as const, label: 'QuantAgent AI', icon: <Cpu className="w-4 h-4" /> },
    { id: 'analytics' as const, label: 'Analytics', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'alerts' as const, label: 'Alerts', icon: <Bell className="w-4 h-4" />, badge: unreadAlertsCount },
    { id: 'disclosures' as const, label: 'PSX Disclosures', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <div className="bg-[#09090b] text-[#fafafa] font-mono selection:bg-[#3b82f6] selection:text-white">

      {/* Navigation Header */}
      <div className="bg-[#0d0d0f] border-b border-[#27272a] sticky top-0 z-40">
        <div className="px-4 py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></div>
              <span className="text-xs font-bold text-[#10b981] uppercase tracking-widest">PSX WorldMonitor</span>
            </div>
            <span className="text-[#3f3f46] hidden sm:inline">|</span>
            <span className="text-[10px] text-[#71717a] hidden sm:inline">Macro & Geopolitical Terminal</span>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:flex-none sm:w-56">
              <input
                type="text"
                placeholder="Search $OGDC, SBP, IMF..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#18181b] border border-[#27272a] rounded px-3 py-1.5 text-[11px] text-[#fafafa] placeholder-[#52525b] focus:outline-none focus:border-[#3b82f6]"
              />
            </div>
            <button
              onClick={handleTriggerScan}
              disabled={isScanningWeb}
              className={`px-3 py-1.5 rounded text-[11px] font-bold flex items-center space-x-1.5 transition-all ${
                isScanningWeb
                  ? 'bg-[#27272a] text-[#71717a] cursor-not-allowed'
                  : 'bg-[#3b82f6] hover:bg-blue-600 text-white'
              }`}
            >
              {isScanningWeb ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Scan className="w-3.5 h-3.5" />}
              <span>{isScanningWeb ? 'Scanning...' : 'AI Scan'}</span>
            </button>
            <button
              onClick={() => setIsExportModalOpen(true)}
              className="px-3 py-1.5 bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] text-[#a1a1aa] hover:text-[#fafafa] rounded text-[11px] font-bold flex items-center space-x-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export</span>
            </button>
          </div>
        </div>

        {/* Tab Bar */}
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

      {/* Macro Ticker */}
      <MacroTickerBanner indicators={macroIndicators} />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {activeTab === 'stream' && (
          <LiveNewsTerminal
            newsItems={newsItems}
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
            isScanningWeb={isScanningWeb}
            onTriggerScan={handleTriggerScan}
          />
        )}

        {activeTab === 'heatmap' && (
          <MarketHeatmap
            onAskAgent={(promptText) => {
              setActiveTab('agent');
              handleSendMessage(promptText);
            }}
          />
        )}

        {activeTab === 'map' && (
          <WorldGeopoliticalMap
            hotspots={hotspots}
            newsItems={newsItems}
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
        newsItems={newsItems}
        macroIndicators={macroIndicators}
        sectorSentiment={sectorSentiment}
      />

    </div>
  );
}
