"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import {
  Search, X, ChevronDown, ChevronUp, ExternalLink, Bookmark,
  Bell, Copy, CheckCircle2, AlertTriangle, Clock, Filter,
  TrendingUp, TrendingDown, Minus, Radio, BarChart2, Globe,
  Zap, BookOpen, Newspaper, Rss, Users, Eye, RefreshCw,
  ArrowUp,
} from "lucide-react";
import type { NewsAnnouncement } from "@/lib/api";

const POLL_INTERVAL_MS = 30_000; // 30 seconds

// ─── Types ────────────────────────────────────────────────────────────────────

type ViewId = "all" | "announcements" | "company_news" | "macro" | "sector" | "geo" | "social" | "watchlist";
type SentimentFilter = "all" | "bullish" | "neutral" | "bearish";
type SortOption = "newest" | "materiality" | "confidence";
type ConfirmFilter = "all" | "confirmed" | "unverified";
type PriorityFilter = "all" | "p0" | "p1" | "p2" | "p3";

interface EnrichedEvent {
  id: number;
  title: string;
  summary: string | null;
  category: string;
  publishedAt: string;           // ISO date string
  ticker: string | null;
  companyName: string | null;
  sentimentScore: number | null; // -1 to +1
  narrativeSentiment: "BULLISH" | "NEUTRAL" | "BEARISH" | "MIXED";
  fundamentalImpact: "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED" | "N/A";
  priority: "P0" | "P1" | "P2" | "P3";
  confirmStatus: "Confirmed" | "Reported" | "Unverified";
  materiality: number;           // 0–100
  confidence: number;            // 0–100
  sourceUrl: string | null;
  viewIds: ViewId[];             // which views this event shows up in
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function deriveEnriched(
  a: NewsAnnouncement,
  companyById: Record<number, { name: string; symbol: string | null }>
): EnrichedEvent {
  const company = a.issuer_id != null ? companyById[a.issuer_id] : null;
  const score = a.sentiment_score ?? 0;

  const narrativeSentiment: EnrichedEvent["narrativeSentiment"] =
    score > 0.3 ? "BULLISH" : score < -0.3 ? "BEARISH" : "NEUTRAL";

  const catMap: Record<string, { priority: EnrichedEvent["priority"]; materiality: number; fundImpact: EnrichedEvent["fundamentalImpact"] }> = {
    results:    { priority: "P1", materiality: 85, fundImpact: "MIXED" },
    payout:     { priority: "P1", materiality: 75, fundImpact: "POSITIVE" },
    regulatory: { priority: "P0", materiality: 90, fundImpact: "MIXED" },
    leadership: { priority: "P2", materiality: 60, fundImpact: "NEUTRAL" },
    operations: { priority: "P2", materiality: 65, fundImpact: "MIXED" },
    general:    { priority: "P3", materiality: 40, fundImpact: "NEUTRAL" },
  };
  const cat = catMap[a.category] ?? { priority: "P3" as const, materiality: 40, fundImpact: "NEUTRAL" as const };

  // Adjust materiality by |sentiment|
  const materialityAdj = Math.min(100, Math.round(cat.materiality + Math.abs(score) * 15));

  const views: ViewId[] = ["all", "announcements"];
  if (["results", "payout", "leadership", "operations"].includes(a.category)) views.push("company_news");

  return {
    id: a.id,
    title: a.title,
    summary: a.summary,
    category: a.category,
    publishedAt: a.published_at,
    ticker: company?.symbol ?? null,
    companyName: company?.name ?? null,
    sentimentScore: a.sentiment_score,
    narrativeSentiment,
    fundamentalImpact: cat.fundImpact,
    priority: cat.priority,
    confirmStatus: "Confirmed",
    materiality: materialityAdj,
    confidence: 82,
    sourceUrl: a.source_url,
    viewIds: views,
  };
}

function relativeTime(isoDate: string): string {
  const d = new Date(isoDate);
  const diffMs = Date.now() - d.getTime();
  const diffH = Math.floor(diffMs / 3_600_000);
  const diffD = Math.floor(diffH / 24);
  if (diffH < 1) return "< 1h ago";
  if (diffH < 24) return `${diffH}h ago`;
  if (diffD < 7) return `${diffD}d ago`;
  return d.toLocaleDateString("en-PK", { day: "numeric", month: "short" });
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const PRIORITY_STYLE: Record<string, string> = {
  P0: "bg-[#ef4444]/15 text-[#ef4444] border-[#ef4444]/30",
  P1: "bg-[#f97316]/15 text-[#f97316] border-[#f97316]/30",
  P2: "bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/30",
  P3: "bg-[#52525b]/20 text-[#a1a1aa] border-[#52525b]/30",
};

const SENTIMENT_STYLE: Record<string, string> = {
  BULLISH: "bg-[#10b981]/10 text-[#10b981]",
  BEARISH: "bg-[#ef4444]/10 text-[#ef4444]",
  NEUTRAL: "bg-[#52525b]/20 text-[#a1a1aa]",
  MIXED:   "bg-[#f59e0b]/10 text-[#f59e0b]",
};

const FUND_IMPACT_STYLE: Record<string, string> = {
  POSITIVE: "bg-[#10b981]/10 text-[#10b981]",
  NEGATIVE: "bg-[#ef4444]/10 text-[#ef4444]",
  NEUTRAL:  "bg-[#52525b]/20 text-[#a1a1aa]",
  MIXED:    "bg-[#f59e0b]/10 text-[#f59e0b]",
  "N/A":    "bg-[#27272a] text-[#71717a]",
};

const CAT_LABEL: Record<string, string> = {
  results: "Results", payout: "Payout / Dividend", regulatory: "Regulatory",
  leadership: "Leadership", operations: "Operations", general: "General",
};

function SentimentIcon({ s }: { s: string }) {
  if (s === "BULLISH") return <TrendingUp className="w-3 h-3" />;
  if (s === "BEARISH") return <TrendingDown className="w-3 h-3" />;
  return <Minus className="w-3 h-3" />;
}

function EventCard({
  event,
  onSave,
  saved,
}: {
  event: EnrichedEvent;
  onSave: (id: number) => void;
  saved: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(window.location.origin + `/news/events/${event.id}`).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 hover:border-[#3b82f6]/30 transition-colors group">
      {/* ── Top row ── */}
      <div className="flex items-start gap-2 flex-wrap mb-2">
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${PRIORITY_STYLE[event.priority]}`}>
          {event.priority}
        </span>
        <span className="text-[9px] px-1.5 py-0.5 rounded border border-[#27272a] text-[#71717a] flex items-center gap-1">
          <CheckCircle2 className="w-2.5 h-2.5 text-[#10b981]" /> {event.confirmStatus}
        </span>
        <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#27272a] text-[#a1a1aa]">
          {CAT_LABEL[event.category] ?? event.category}
        </span>
        <span className="ml-auto text-[10px] text-[#52525b] flex items-center gap-1">
          <Clock className="w-3 h-3" /> {relativeTime(event.publishedAt)}
        </span>
      </div>

      {/* ── Headline ── */}
      <h3 className="text-sm font-semibold text-[#fafafa] leading-snug mb-1">{event.title}</h3>

      {/* ── Entity ── */}
      {(event.ticker || event.companyName) && (
        <p className="text-[11px] text-[#71717a] mb-2">
          {event.companyName}{event.ticker ? ` · ${event.ticker}` : ""} · PSX Official Announcements
        </p>
      )}

      {/* ── Signal chips ── */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-medium ${SENTIMENT_STYLE[event.narrativeSentiment]}`}>
          <SentimentIcon s={event.narrativeSentiment} />
          Narrative: {event.narrativeSentiment.charAt(0) + event.narrativeSentiment.slice(1).toLowerCase()}
        </span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${FUND_IMPACT_STYLE[event.fundamentalImpact]}`}>
          Fundamental: {event.fundamentalImpact.charAt(0) + event.fundamentalImpact.slice(1).toLowerCase()}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1c1c1e] border border-[#27272a] text-[#71717a]">
          Materiality {event.materiality}/100
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1c1c1e] border border-[#27272a] text-[#71717a]">
          Confidence {event.confidence}%
        </span>
      </div>

      {/* ── Summary (expandable) ── */}
      {event.summary && (
        <div className="mb-3">
          <p className={`text-[11px] text-[#a1a1aa] leading-relaxed ${expanded ? "" : "line-clamp-2"}`}>
            {event.summary}
          </p>
          <button
            onClick={() => setExpanded(v => !v)}
            className="text-[10px] text-[#3b82f6] hover:underline mt-0.5 flex items-center gap-0.5"
          >
            {expanded ? <><ChevronUp className="w-3 h-3" /> Show less</> : <><ChevronDown className="w-3 h-3" /> Read more</>}
          </button>
        </div>
      )}

      {/* ── Actions ── */}
      <div className="flex items-center gap-2 pt-2 border-t border-[#27272a]">
        <button
          onClick={() => onSave(event.id)}
          className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded transition-colors ${saved ? "text-[#3b82f6] bg-[#3b82f6]/10" : "text-[#71717a] hover:text-[#a1a1aa] hover:bg-[#27272a]"}`}
        >
          <Bookmark className="w-3 h-3" /> {saved ? "Saved" : "Save"}
        </button>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[10px] px-2 py-1 rounded text-[#71717a] hover:text-[#a1a1aa] hover:bg-[#27272a] transition-colors"
        >
          <Copy className="w-3 h-3" /> {copied ? "Copied!" : "Copy link"}
        </button>
        <button className="flex items-center gap-1 text-[10px] px-2 py-1 rounded text-[#71717a] hover:text-[#a1a1aa] hover:bg-[#27272a] transition-colors">
          <Bell className="w-3 h-3" /> Alert
        </button>
        {event.sourceUrl && (
          <a
            href={event.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto flex items-center gap-1 text-[10px] px-2 py-1 rounded text-[#3b82f6] hover:bg-[#3b82f6]/10 transition-colors"
          >
            <ExternalLink className="w-3 h-3" /> Open source
          </a>
        )}
      </div>
    </article>
  );
}

// ─── View selector config ─────────────────────────────────────────────────────

const VIEWS: { id: ViewId; label: string; icon: React.ReactNode; desc: string }[] = [
  { id: "all",           label: "All",           icon: <Rss className="w-3.5 h-3.5" />,       desc: "All approved events" },
  { id: "announcements", label: "Announcements", icon: <Radio className="w-3.5 h-3.5" />,     desc: "PSX & issuer official" },
  { id: "company_news",  label: "Company News",  icon: <Newspaper className="w-3.5 h-3.5" />, desc: "Company-level events" },
  { id: "macro",         label: "Macro & Policy", icon: <BarChart2 className="w-3.5 h-3.5" />, desc: "SBP, GoP, budget, IMF" },
  { id: "sector",        label: "Sector Data",   icon: <TrendingUp className="w-3.5 h-3.5" />, desc: "NFDC, PAMA, utilization" },
  { id: "geo",           label: "Geopolitics",   icon: <Globe className="w-3.5 h-3.5" />,      desc: "Cross-border read-throughs" },
  { id: "social",        label: "Social Pulse",  icon: <Users className="w-3.5 h-3.5" />,      desc: "Attention & rumor monitor" },
  { id: "watchlist",     label: "My Watchlist",  icon: <BookOpen className="w-3.5 h-3.5" />,   desc: "Saved watchlist events" },
];

// ─── Main component ───────────────────────────────────────────────────────────

interface NewsTabProps {
  announcements: NewsAnnouncement[];
  companyById: Record<number, { name: string; symbol: string | null }>;
}

export function NewsTab({ announcements, companyById }: NewsTabProps) {
  const [activeView, setActiveView] = useState<ViewId>("all");
  const [keyword, setKeyword] = useState("");
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>("all");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");
  const [confirmFilter] = useState<ConfirmFilter>("all");
  const [tickerFilter, setTickerFilter] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [dateRange, setDateRange] = useState<"7d" | "30d" | "90d" | "all">("all");
  const [showFilters, setShowFilters] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());

  // ── Real-time state ────────────────────────────────────────────────────────
  const [liveData, setLiveData] = useState<NewsAnnouncement[]>(announcements);
  const [pendingItems, setPendingItems] = useState<NewsAnnouncement[]>([]);
  // Initialized null to avoid SSR/client hydration mismatch — new Date() must
  // only ever be computed client-side, after mount.
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollError, setPollError] = useState(false);
  const knownIdsRef = useRef<Set<number>>(new Set(announcements.map(a => a.id)));

  // Poll every 30 seconds for new announcements
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    const poll = async () => {
      setIsPolling(true);
      setPollError(false);
      try {
        const res = await fetch(`${apiBase}/news/announcements`, { cache: "no-store" });
        if (!res.ok) { setPollError(true); return; }
        const fresh: NewsAnnouncement[] = await res.json();
        const newItems = fresh.filter(a => !knownIdsRef.current.has(a.id));
        if (newItems.length > 0) {
          setPendingItems(prev => [...newItems, ...prev]);
          newItems.forEach(a => knownIdsRef.current.add(a.id));
        }
        // Also replace full data to pick up updated fields
        setLiveData(fresh);
        setLastUpdated(new Date());
      } catch {
        setPollError(true);
      } finally {
        setIsPolling(false);
      }
    };

    const id = setInterval(poll, POLL_INTERVAL_MS);
    // Kick off immediately on mount too
    poll();
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPending = useCallback(() => {
    setLiveData(prev => {
      const existingIds = new Set(prev.map(a => a.id));
      const toAdd = pendingItems.filter(a => !existingIds.has(a.id));
      return [...toAdd, ...prev];
    });
    setPendingItems([]);
  }, [pendingItems]);

  const manualRefresh = useCallback(async () => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    setIsPolling(true);
    setPollError(false);
    try {
      const res = await fetch(`${apiBase}/news/announcements`, { cache: "no-store" });
      if (!res.ok) { setPollError(true); return; }
      const fresh: NewsAnnouncement[] = await res.json();
      setLiveData(fresh);
      fresh.forEach(a => knownIdsRef.current.add(a.id));
      setPendingItems([]);
      setLastUpdated(new Date());
    } catch {
      setPollError(true);
    } finally {
      setIsPolling(false);
    }
  }, []);

  // ── Enrich all announcements once ─────────────────────────────────────────
  const allEvents = useMemo(
    () => liveData.map(a => deriveEnriched(a, companyById)),
    [liveData, companyById]
  );

  // ── Pulse strip metrics ────────────────────────────────────────────────────
  const p0Count = useMemo(() => allEvents.filter(e => e.priority === "P0").length, [allEvents]);
  const p1Count = useMemo(() => allEvents.filter(e => e.priority === "P1").length, [allEvents]);
  const verifiedCount = useMemo(() => allEvents.filter(e => e.confirmStatus === "Confirmed").length, [allEvents]);

  const dominantNarrative = useMemo(() => {
    const counts = { BULLISH: 0, BEARISH: 0, NEUTRAL: 0, MIXED: 0 };
    allEvents.forEach(e => counts[e.narrativeSentiment]++);
    return (Object.entries(counts) as [string, number][]).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "NEUTRAL";
  }, [allEvents]);

  const divergenceCount = useMemo(
    () => allEvents.filter(e =>
      (e.narrativeSentiment === "BULLISH" && e.fundamentalImpact === "NEGATIVE") ||
      (e.narrativeSentiment === "BEARISH" && e.fundamentalImpact === "POSITIVE")
    ).length,
    [allEvents]
  );

  // ── Filtering & sorting ────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    let result = allEvents;

    // View filter
    if (activeView !== "all") {
      result = result.filter(e => e.viewIds.includes(activeView));
    }

    // Date range
    if (dateRange !== "all") {
      const days = dateRange === "7d" ? 7 : dateRange === "30d" ? 30 : 90;
      const cutoff = Date.now() - days * 86_400_000;
      result = result.filter(e => new Date(e.publishedAt).getTime() >= cutoff);
    }

    // Keyword
    if (keyword.trim()) {
      const kw = keyword.trim().toLowerCase();
      result = result.filter(e =>
        e.title.toLowerCase().includes(kw) ||
        (e.summary ?? "").toLowerCase().includes(kw) ||
        (e.ticker ?? "").toLowerCase().includes(kw) ||
        (e.companyName ?? "").toLowerCase().includes(kw)
      );
    }

    // Ticker
    if (tickerFilter.trim()) {
      const t = tickerFilter.trim().toUpperCase();
      result = result.filter(e => e.ticker?.toUpperCase().includes(t) || e.companyName?.toUpperCase().includes(t));
    }

    // Sentiment
    if (sentimentFilter !== "all") {
      const map: Record<SentimentFilter, string> = {
        all: "", bullish: "BULLISH", bearish: "BEARISH", neutral: "NEUTRAL",
      };
      result = result.filter(e => e.narrativeSentiment === map[sentimentFilter]);
    }

    // Priority
    if (priorityFilter !== "all") {
      result = result.filter(e => e.priority === priorityFilter.toUpperCase());
    }

    // Confirmation
    if (confirmFilter === "confirmed") result = result.filter(e => e.confirmStatus === "Confirmed");
    if (confirmFilter === "unverified") result = result.filter(e => e.confirmStatus === "Unverified");

    // Sort
    if (sortBy === "newest") result = [...result].sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
    if (sortBy === "materiality") result = [...result].sort((a, b) => b.materiality - a.materiality);
    if (sortBy === "confidence") result = [...result].sort((a, b) => b.confidence - a.confidence);

    return result;
  }, [allEvents, activeView, dateRange, keyword, tickerFilter, sentimentFilter, priorityFilter, confirmFilter, sortBy]);

  // ── Top themes for right rail ──────────────────────────────────────────────
  const topThemes = useMemo(() => {
    const freq: Record<string, number> = {};
    allEvents.forEach(e => { freq[e.category] = (freq[e.category] ?? 0) + 1; });
    return (Object.entries(freq) as [string, number][])
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cat, count]) => ({ cat, count }));
  }, [allEvents]);

  // ── Priority queue for right rail ─────────────────────────────────────────
  const priorityQueue = useMemo(
    () => allEvents.filter(e => e.priority === "P0" || e.priority === "P1").slice(0, 5),
    [allEvents]
  );

  const handleSave = useCallback((id: number) => {
    setSavedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const hasActiveFilters = keyword || tickerFilter || sentimentFilter !== "all" || priorityFilter !== "all" || dateRange !== "all";

  const clearFilters = () => {
    setKeyword(""); setTickerFilter(""); setSentimentFilter("all");
    setPriorityFilter("all"); setDateRange("all");
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-0 min-h-0">

      {/* ── Pulse strip ─────────────────────────────────────────────────── */}
      <div className="bg-[#0d0d0f] border-b border-[#27272a] px-4 py-2">
        <div className="flex items-center gap-4 flex-wrap text-[10px] font-mono">
          {/* Live indicator */}
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isPolling ? "bg-[#3b82f6] animate-pulse" : pollError ? "bg-[#ef4444]" : "bg-[#10b981] animate-pulse"}`} />
            <span className={`font-bold ${pollError ? "text-[#ef4444]" : "text-[#10b981]"}`}>
              {pollError ? "OFFLINE" : "LIVE"}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#ef4444]" />
            <span className="text-[#ef4444] font-bold">P0 {p0Count}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#f97316]" />
            <span className="text-[#f97316] font-bold">P1 {p1Count}</span>
          </div>
          <span className="text-[#52525b]">|</span>
          <span className="text-[#71717a]">
            <span className="text-[#10b981]">{verifiedCount}</span> verified
          </span>
          <span className="text-[#52525b]">|</span>
          <span className="text-[#71717a]">Dominant narrative:
            <span className={`ml-1 font-bold ${dominantNarrative === "BULLISH" ? "text-[#10b981]" : dominantNarrative === "BEARISH" ? "text-[#ef4444]" : "text-[#a1a1aa]"}`}>
              {dominantNarrative}
            </span>
          </span>
          {divergenceCount > 0 && (
            <>
              <span className="text-[#52525b]">|</span>
              <span className="text-[#f59e0b] flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> {divergenceCount} divergence
              </span>
            </>
          )}
          <span className="text-[#52525b]">|</span>
          <span className="text-[#52525b]">{allEvents.length} events · PSX Official</span>

          {/* Last updated + refresh */}
          <span className="ml-auto flex items-center gap-2 text-[#52525b]">
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" /> {filtered.length} visible
            </span>
            <span>·</span>
            <span>{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}` : "Connecting…"}</span>
            <button
              onClick={manualRefresh}
              disabled={isPolling}
              title="Refresh now"
              className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-[#27272a] hover:text-[#a1a1aa] transition-colors disabled:opacity-40"
            >
              <RefreshCw className={`w-3 h-3 ${isPolling ? "animate-spin text-[#3b82f6]" : ""}`} />
            </button>
          </span>
        </div>
      </div>

      {/* ── New items banner ─────────────────────────────────────────────── */}
      {pendingItems.length > 0 && (
        <button
          onClick={loadPending}
          className="w-full bg-[#3b82f6]/10 border-b border-[#3b82f6]/30 py-2 px-4 text-[11px] font-bold text-[#3b82f6] hover:bg-[#3b82f6]/20 transition-colors flex items-center justify-center gap-2"
        >
          <ArrowUp className="w-3.5 h-3.5" />
          {pendingItems.length} new item{pendingItems.length !== 1 ? "s" : ""} — click to load
        </button>
      )}

      {/* ── View selector ───────────────────────────────────────────────── */}
      <div className="bg-[#0d0d0f] border-b border-[#27272a] px-4 overflow-x-auto">
        <div className="flex items-center gap-0.5 py-1 min-w-max">
          {VIEWS.map(view => {
            const count = view.id === "all" ? allEvents.length : allEvents.filter(e => e.viewIds.includes(view.id)).length;
            return (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                title={view.desc}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-[10px] font-bold transition-colors whitespace-nowrap ${
                  activeView === view.id
                    ? "bg-[#3b82f6]/15 text-[#3b82f6]"
                    : "text-[#71717a] hover:text-[#a1a1aa] hover:bg-[#27272a]"
                }`}
              >
                {view.icon}
                {view.label}
                <span className={`text-[9px] px-1 rounded ${activeView === view.id ? "bg-[#3b82f6]/20 text-[#3b82f6]" : "bg-[#27272a] text-[#52525b]"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Search + filter bar ──────────────────────────────────────────── */}
      <div className="bg-[#111113] border-b border-[#27272a] px-4 py-2.5 space-y-2">
        <div className="flex items-center gap-2">
          {/* Keyword search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#52525b]" />
            <input
              type="text"
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              placeholder="Search headlines, tickers, summaries…"
              className="w-full bg-[#18181b] border border-[#27272a] rounded px-3 py-1.5 pl-8 text-[11px] text-[#fafafa] placeholder-[#52525b] focus:outline-none focus:border-[#3b82f6]/60"
            />
            {keyword && <button onClick={() => setKeyword("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#52525b] hover:text-[#a1a1aa]"><X className="w-3 h-3" /></button>}
          </div>

          {/* Ticker filter */}
          <input
            type="text"
            value={tickerFilter}
            onChange={e => setTickerFilter(e.target.value)}
            placeholder="Ticker / company"
            className="bg-[#18181b] border border-[#27272a] rounded px-3 py-1.5 text-[11px] text-[#fafafa] placeholder-[#52525b] focus:outline-none focus:border-[#3b82f6]/60 w-36"
          />

          {/* Toggle filter drawer */}
          <button
            onClick={() => setShowFilters(v => !v)}
            className={`flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded border transition-colors ${
              showFilters ? "bg-[#3b82f6]/10 border-[#3b82f6]/30 text-[#3b82f6]" : "bg-[#18181b] border-[#27272a] text-[#71717a] hover:text-[#a1a1aa]"
            }`}
          >
            <Filter className="w-3.5 h-3.5" /> Filters {hasActiveFilters && <span className="w-1.5 h-1.5 rounded-full bg-[#3b82f6]" />}
          </button>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortOption)}
            className="bg-[#18181b] border border-[#27272a] rounded px-2 py-1.5 text-[11px] text-[#a1a1aa] focus:outline-none"
          >
            <option value="newest">Newest first</option>
            <option value="materiality">Highest materiality</option>
            <option value="confidence">Highest confidence</option>
          </select>
        </div>

        {/* Expanded filter drawer */}
        {showFilters && (
          <div className="flex flex-wrap gap-3 pt-2 border-t border-[#27272a]">
            {/* Sentiment */}
            <div className="space-y-1">
              <p className="text-[9px] text-[#52525b] uppercase tracking-wider">Narrative Sentiment</p>
              <div className="flex gap-1">
                {(["all", "bullish", "neutral", "bearish"] as SentimentFilter[]).map(s => (
                  <button key={s} onClick={() => setSentimentFilter(s)}
                    className={`text-[10px] px-2 py-0.5 rounded capitalize transition-colors ${sentimentFilter === s ? "bg-[#3b82f6] text-white" : "bg-[#27272a] text-[#71717a] hover:text-[#a1a1aa]"}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Priority */}
            <div className="space-y-1">
              <p className="text-[9px] text-[#52525b] uppercase tracking-wider">Priority</p>
              <div className="flex gap-1">
                {(["all", "p0", "p1", "p2", "p3"] as PriorityFilter[]).map(p => (
                  <button key={p} onClick={() => setPriorityFilter(p)}
                    className={`text-[10px] px-2 py-0.5 rounded uppercase transition-colors ${priorityFilter === p ? "bg-[#3b82f6] text-white" : "bg-[#27272a] text-[#71717a] hover:text-[#a1a1aa]"}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Date range */}
            <div className="space-y-1">
              <p className="text-[9px] text-[#52525b] uppercase tracking-wider">Date Range</p>
              <div className="flex gap-1">
                {(["7d", "30d", "90d", "all"] as const).map(d => (
                  <button key={d} onClick={() => setDateRange(d)}
                    className={`text-[10px] px-2 py-0.5 rounded transition-colors ${dateRange === d ? "bg-[#3b82f6] text-white" : "bg-[#27272a] text-[#71717a] hover:text-[#a1a1aa]"}`}>
                    {d === "all" ? "All time" : d}
                  </button>
                ))}
              </div>
            </div>

            {hasActiveFilters && (
              <button onClick={clearFilters} className="text-[10px] text-[#ef4444] hover:underline self-end ml-auto flex items-center gap-1">
                <X className="w-3 h-3" /> Clear all
              </button>
            )}
          </div>
        )}

        {/* Active filter chips */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {keyword && <Chip label={`"${keyword}"`} onRemove={() => setKeyword("")} />}
            {tickerFilter && <Chip label={tickerFilter.toUpperCase()} onRemove={() => setTickerFilter("")} />}
            {sentimentFilter !== "all" && <Chip label={sentimentFilter} onRemove={() => setSentimentFilter("all")} />}
            {priorityFilter !== "all" && <Chip label={priorityFilter.toUpperCase()} onRemove={() => setPriorityFilter("all")} />}
            {dateRange !== "all" && <Chip label={dateRange} onRemove={() => setDateRange("all")} />}
          </div>
        )}
      </div>

      {/* ── Main layout: feed + right rail ──────────────────────────────── */}
      <div className="flex gap-0 flex-1 min-h-0">

        {/* Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-w-0">
          {filtered.length === 0 ? (
            <EmptyState view={activeView} hasFilters={!!hasActiveFilters} onClear={clearFilters} />
          ) : (
            <>
              <p className="text-[10px] text-[#52525b] font-mono">
                {filtered.length} event{filtered.length !== 1 ? "s" : ""} · sorted by {sortBy === "newest" ? "publication time" : sortBy}
              </p>
              {filtered.map(event => (
                <EventCard key={event.id} event={event} onSave={handleSave} saved={savedIds.has(event.id)} />
              ))}
            </>
          )}
        </div>

        {/* Right rail */}
        <aside className="w-72 shrink-0 border-l border-[#27272a] p-4 space-y-5 overflow-y-auto hidden xl:block">

          {/* Priority queue */}
          <div>
            <h4 className="text-[10px] font-bold text-[#71717a] uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Zap className="w-3 h-3 text-[#f97316]" /> Priority Queue
            </h4>
            {priorityQueue.length === 0 ? (
              <p className="text-[10px] text-[#52525b]">No P0/P1 events</p>
            ) : (
              <div className="space-y-2">
                {priorityQueue.map(e => (
                  <div key={e.id} className="bg-[#18181b] border border-[#27272a] rounded p-2.5 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[9px] font-bold px-1 py-0.5 rounded border ${PRIORITY_STYLE[e.priority]}`}>{e.priority}</span>
                      <span className="text-[9px] text-[#52525b]">{relativeTime(e.publishedAt)}</span>
                    </div>
                    <p className="text-[11px] text-[#fafafa] line-clamp-2 leading-snug">{e.title}</p>
                    {e.ticker && <p className="text-[10px] text-[#71717a]">{e.ticker}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top themes */}
          <div>
            <h4 className="text-[10px] font-bold text-[#71717a] uppercase tracking-wider mb-2">Top Themes</h4>
            <div className="space-y-1.5">
              {topThemes.map(({ cat, count }) => (
                <div key={cat} className="flex items-center justify-between text-[11px]">
                  <span className="text-[#a1a1aa] capitalize">{CAT_LABEL[cat] ?? cat}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-[#27272a] rounded-full h-1">
                      <div
                        className="bg-[#3b82f6] h-1 rounded-full"
                        style={{ width: `${(count / (allEvents.length || 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-[#52525b] w-4 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sentiment divergence */}
          {divergenceCount > 0 && (
            <div className="bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-lg p-3">
              <h4 className="text-[10px] font-bold text-[#f59e0b] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3" /> Divergence Signal
              </h4>
              <p className="text-[11px] text-[#a1a1aa]">
                {divergenceCount} event{divergenceCount !== 1 ? "s" : ""} where narrative sentiment and fundamental impact point in opposite directions. Review evidence before acting.
              </p>
            </div>
          )}

          {/* Saved events */}
          {savedIds.size > 0 && (
            <div>
              <h4 className="text-[10px] font-bold text-[#71717a] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Bookmark className="w-3 h-3 text-[#3b82f6]" /> Saved ({savedIds.size})
              </h4>
              <div className="space-y-1.5">
                {allEvents.filter(e => savedIds.has(e.id)).slice(0, 4).map(e => (
                  <p key={e.id} className="text-[11px] text-[#a1a1aa] line-clamp-2 leading-snug">{e.title}</p>
                ))}
              </div>
            </div>
          )}

          {/* Source health */}
          <div>
            <h4 className="text-[10px] font-bold text-[#71717a] uppercase tracking-wider mb-2">Source Health</h4>
            <div className="space-y-1.5">
              {[
                { name: "PSX Official Announcements", ok: true },
                { name: "SBP EasyData", ok: true },
                { name: "Licensed news feed", ok: false },
                { name: "Social pulse", ok: false },
              ].map(s => (
                <div key={s.name} className="flex items-center gap-2 text-[10px]">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${s.ok ? "bg-[#10b981]" : "bg-[#27272a]"}`} />
                  <span className={s.ok ? "text-[#a1a1aa]" : "text-[#52525b]"}>{s.name}</span>
                  {!s.ok && <span className="text-[#52525b] ml-auto">not connected</span>}
                </div>
              ))}
            </div>
          </div>

        </aside>
      </div>
    </div>
  );
}

// ─── Chip ─────────────────────────────────────────────────────────────────────

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-[#3b82f6]/10 border border-[#3b82f6]/20 rounded text-[#3b82f6]">
      {label}
      <button onClick={onRemove} className="hover:text-[#ef4444] transition-colors"><X className="w-2.5 h-2.5" /></button>
    </span>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState({ view, hasFilters, onClear }: { view: ViewId; hasFilters: boolean; onClear: () => void }) {
  const viewCopy: Record<ViewId, { icon: string; msg: string }> = {
    all:           { icon: "📭", msg: "No events yet. Ensure the backend is running." },
    announcements: { icon: "📋", msg: "No official announcements found." },
    company_news:  { icon: "🏢", msg: "No company news events in the current range." },
    macro:         { icon: "📊", msg: "Macro & Policy adapter not yet connected in v1." },
    sector:        { icon: "⚙️",  msg: "Sector data adapter not yet connected in v1." },
    geo:           { icon: "🌍", msg: "Geopolitical feed not yet connected in v1." },
    social:        { icon: "📱", msg: "Social pulse adapter not yet connected in v1." },
    watchlist:     { icon: "⭐", msg: "Save events to populate your watchlist." },
  };
  const copy = viewCopy[view];
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <span className="text-3xl">{copy.icon}</span>
      <p className="text-sm text-[#71717a]">{copy.msg}</p>
      {hasFilters && (
        <button onClick={onClear} className="text-[11px] text-[#3b82f6] hover:underline">Clear filters</button>
      )}
    </div>
  );
}
