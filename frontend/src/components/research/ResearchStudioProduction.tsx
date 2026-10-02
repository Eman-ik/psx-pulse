"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";
import type { SearchResult } from "@/lib/studio-api";
import { Fundamentals } from "@/components/research/Fundamentals";
import { ResearchIntelligenceDashboard } from "@/components/ResearchIntelligence";
import { BusinessTab, GovernanceTab } from "./studio/BusinessTab";
import { EventsTab } from "./studio/EventsTab";
import { EvidenceTab } from "./studio/EvidenceTab";
import { OverviewTab } from "./studio/OverviewTab";
import { PeersTab } from "./studio/PeersTab";
import { TechnicalsTab } from "./studio/TechnicalsTab";
import { ValuationTab } from "./studio/ValuationTab";
import { Card, day, Label, num } from "./studio/ui";
import TradePlanningView from "./TradePlanningView";

const TABS = [
  ["overview", "Overview"],
  ["intelligence", "Intelligence"],
  ["business", "Business"],
  ["financials", "Financials"],
  ["valuation", "Valuation"],
  ["technicals", "Technicals"],
  ["trade", "Trade Plan"],
  ["events", "News & events"],
  ["peers", "Peers"],
  ["governance", "Governance"],
  ["evidence", "Evidence"],
] as const;
type TabId = (typeof TABS)[number][0];

const DEFAULT_SYMBOL = "FFC";

function CompanySearch({ onSelect }: { onSelect: (symbol: string) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults([]);
      return;
    }
    const timer = setTimeout(() => {
      fetch(`${API_BASE_URL}/api/v1/companies/search?q=${encodeURIComponent(q)}`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d) => setResults(d.results))
        .catch(() => setResults([]));
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const close = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const pick = (symbol: string) => {
    onSelect(symbol);
    setQuery("");
    setOpen(false);
  };

  return (
    <div ref={box} className="relative w-full sm:max-w-md">
      <label className="relative block">
        <span className="sr-only">Search companies by ticker or name</span>
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && results[0]) pick(results[0].symbol);
            if (e.key === "Escape") setOpen(false);
          }}
          placeholder="Search ticker or company"
          role="combobox"
          aria-expanded={open && results.length > 0}
          aria-controls="company-results"
          className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
      </label>
      {open && results.length > 0 && (
        <ul id="company-results" role="listbox" className="absolute z-50 mt-1 w-full overflow-hidden rounded-lg border border-border bg-[#f4f6fa] shadow-lg">
          {results.map((r) => (
            <li key={r.security_id} role="option" aria-selected={false}>
              <button type="button" onClick={() => pick(r.symbol)} className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-accent/10">
                <span>
                  <span className="font-semibold">{r.symbol}</span> <span className="text-muted">{r.name}</span>
                  <span className="block text-xs text-muted">{r.sector ?? "No sector"}</span>
                </span>
                <span className="text-right text-xs">
                  {r.price.close == null ? "No price" : num(r.price.close)}
                  <span className="block text-muted">{r.price.freshness.stale ? "stale" : day(r.price.freshness.as_of)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ResearchStudioProduction() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const symbol = (params.get("t") ?? DEFAULT_SYMBOL).toUpperCase();
  const requested = params.get("tab");
  const tab: TabId = TABS.some(([id]) => id === requested) ? (requested as TabId) : "overview";

  const go = (next: { t?: string; tab?: TabId }) => {
    const q = new URLSearchParams(params.toString());
    q.set("t", next.t ?? symbol);
    q.set("tab", next.tab ?? (next.t ? "overview" : tab));
    router.replace(`${pathname}?${q.toString()}`, { scroll: false });
  };

  const onTabKey = (e: React.KeyboardEvent) => {
    const i = TABS.findIndex(([id]) => id === tab);
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (step) {
      e.preventDefault();
      go({ tab: TABS[(i + step + TABS.length) % TABS.length][0] });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/40">
        <div className="mx-auto max-w-6xl px-4 pt-6 sm:px-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Equity Research Studio</h1>
              <p className="text-xs text-muted">
                <Label kind="VERIFIED" /> source-backed data only; anything missing is shown as missing
              </p>
            </div>
            <CompanySearch onSelect={(s) => go({ t: s })} />
          </div>
          <div role="tablist" aria-label="Research sections" onKeyDown={onTabKey} className="-mb-px flex gap-1 overflow-x-auto">
            {TABS.map(([id, label]) => (
              <button
                key={id}
                role="tab"
                id={`tab-${id}`}
                aria-selected={tab === id}
                aria-controls="studio-panel"
                tabIndex={tab === id ? 0 : -1}
                onClick={() => go({ tab: id })}
                className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition ${
                  tab === id ? "border-accent text-accent" : "border-transparent text-muted hover:text-foreground"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main id="studio-panel" role="tabpanel" aria-labelledby={`tab-${tab}`} className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <p className="mb-4 text-xs text-muted">
          Viewing <span className="font-semibold text-foreground">{symbol}</span>. Research evidence, not a recommendation.
        </p>
        {tab === "overview" && <OverviewTab symbol={symbol} onOpenTab={(t) => go({ tab: t as TabId })} />}
        {tab === "intelligence" && <ResearchIntelligenceDashboard ticker={symbol} apiUrl={API_BASE_URL} />}
        {tab === "business" && <BusinessTab symbol={symbol} />}
        {tab === "financials" && (
          <Card title="Financial statements and ratios">
            <Fundamentals symbol={symbol} api={API_BASE_URL} />
          </Card>
        )}
        {tab === "valuation" && <ValuationTab symbol={symbol} />}
        {tab === "technicals" && <TechnicalsTab symbol={symbol} />}
        {tab === "trade" && <TradePlanningView ticker={symbol} />}
        {tab === "events" && <EventsTab symbol={symbol} />}
        {tab === "peers" && <PeersTab symbol={symbol} />}
        {tab === "governance" && <GovernanceTab symbol={symbol} />}
        {tab === "evidence" && <EvidenceTab symbol={symbol} />}
      </main>
    </div>
  );
}
