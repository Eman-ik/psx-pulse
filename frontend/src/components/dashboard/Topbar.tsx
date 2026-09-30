"use client";

import { Search, Bell, BarChart2 } from "lucide-react";
import { useLiveQuotes } from "@/lib/useLiveQuotes";

export default function Topbar({ isLive: isLiveOverride }: { isLive?: boolean }) {
  const { isLive: liveFromHook, loading } = useLiveQuotes({ skip: isLiveOverride !== undefined });
  const isLive = isLiveOverride ?? liveFromHook;

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-white/60 bg-[rgba(255,255,255,0.65)] backdrop-blur-xl px-6 py-3.5 lg:px-8 shadow-xs">
      <div>
        <p className="text-[11px] font-medium text-[#566680]">
          Homepage / <span className="text-[#10161A] font-semibold">Fertilizer Intelligence</span>
        </p>
        <h1 className="text-lg font-bold tracking-tight text-[#10161A]">PSX Sector Dashboard</h1>
      </div>

      <div className="flex flex-1 items-center justify-end gap-3">
        <div className="hidden max-w-xs flex-1 items-center gap-2.5 rounded-full border border-white/80 bg-white/70 px-4 py-1.5 shadow-2xs backdrop-blur-md sm:flex focus-within:border-[#566680]/50 transition-colors">
          <Search size={14} className="text-[#566680]" />
          <input
            type="text"
            placeholder="Search companies, tickers, announcements..."
            className="w-full bg-transparent text-xs text-[#10161A] placeholder:text-[#8E9CB7] focus:outline-none"
          />
        </div>

        <span
          className={`hidden rounded-full border px-3 py-1 text-[11px] font-medium sm:inline-flex items-center gap-1.5 ${
            loading
              ? "border-[#566680]/20 bg-[#B4C0D5]/20 text-[#566680]"
              : isLive
                ? "border-[#566680]/30 bg-[#B4C0D5]/35 text-[#10161A]"
                : "border-[#8E9CB7]/40 bg-white/70 text-[#566680]"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${isLive ? "bg-[#10161A]" : "bg-[#8E9CB7]"}`} />
          {loading ? "Syncing quotes…" : isLive ? "Live prices via psxdata" : "EOD Verified Data"}
        </span>

        <button
          aria-label="Alerts"
          className="relative flex h-8 w-8 items-center justify-center rounded-full border border-white/80 bg-white/70 text-[#566680] hover:text-[#10161A] hover:bg-white transition-all shadow-2xs"
        >
          <Bell size={14} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#10161A]" />
        </button>

        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#10161A] text-[#DAE1EE] shadow-sm">
          <BarChart2 size={14} />
        </div>
      </div>
    </header>
  );
}
