"use client";

import { Search, Bell, BarChart2 } from "lucide-react";
import { useLiveQuotes } from "@/lib/useLiveQuotes";

/**
 * isLive is optional: pages that already know their own live-data status (or that show
 * no live data at all, e.g. Research/Portfolio) can still pass it explicitly. Everyone
 * else gets it for free from useLiveQuotes() -- this used to mean every one of those
 * pages awaited its own fetchLiveQuotes() call during SSR just to compute this badge
 * (up to 35s), which is the whole reason the badge now resolves client-side instead.
 */
export default function Topbar({ isLive: isLiveOverride }: { isLive?: boolean }) {
  const { isLive: liveFromHook, loading } = useLiveQuotes({ skip: isLiveOverride !== undefined });
  const isLive = isLiveOverride ?? liveFromHook;
  return (
    <header className="flex items-center justify-between gap-4 border-b border-border px-6 py-4 lg:px-8">
      <div>
        <p className="text-xs text-muted">
          Homepage / <span className="text-foreground">Dashboard</span>
        </p>
        <h1 className="text-xl font-semibold">PSX Research</h1>
      </div>

      <div className="flex flex-1 items-center justify-end gap-3">
        <div className="hidden max-w-xs flex-1 items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 sm:flex">
          <Search size={15} className="text-muted" />
          <input
            type="text"
            placeholder="Search companies, tickers..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
          />
        </div>

        <span
          className={`hidden rounded-full border px-3 py-1.5 text-xs font-medium sm:inline-block ${
            loading
              ? "border-border bg-surface-alt text-muted"
              : isLive
                ? "border-positive/30 bg-positive/10 text-positive"
                : "border-accent-yellow/30 bg-accent-yellow/10 text-accent-yellow"
          }`}
        >
          {loading ? "Loading live prices…" : isLive ? "Live prices via psxdata" : "Sample data — not live"}
        </span>

        <button className="relative flex h-9 w-9 items-center justify-center rounded-full border border-border bg-surface text-muted hover:text-foreground">
          <Bell size={16} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-negative" />
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/15 text-accent">
          <BarChart2 size={16} />
        </div>
      </div>
    </header>
  );
}
