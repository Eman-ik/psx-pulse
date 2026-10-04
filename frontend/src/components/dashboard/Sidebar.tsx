"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SlidersHorizontal,
  GraduationCap,
  Bell,
  Settings,
  HelpCircle,
  LogOut,
  BarChart2,
  FileSearch,
} from "lucide-react";

const mainNav = [
  { label: "Dashboard", icon: BarChart2, href: "/" },
  { label: "Market Overview", icon: BarChart2, href: "/market" },
  { label: "Research Studio", icon: FileSearch, href: "/research" },
  { label: "Screeners", icon: SlidersHorizontal, href: "/screening" },
  { label: "Academy", icon: GraduationCap, href: "#", disabled: true },
  { label: "Watchlists & Alerts", icon: Bell, href: "#", disabled: true },
];

const screenerTypes = [
  { label: "Fundamental Screening", href: "/screening" },
  { label: "Technical Analysis", href: "/technical" },
  { label: "Momentum Analysis", href: "/momentum" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col justify-between border-r border-white/60 bg-[rgba(218,225,238,0.75)] backdrop-blur-xl px-5 py-6">
      <div>
        <div className="mb-8 flex items-center gap-2.5 px-1">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#10161A] text-[#DAE1EE] shadow-sm">
            <BarChart2 size={16} />
          </span>
          <div className="flex flex-col">
            <span className="text-base font-bold tracking-tight text-[#10161A]">
              PSX<span className="text-[#566680] font-medium ml-1">Pulse</span>
            </span>
            <span className="text-[10px] uppercase font-mono tracking-widest text-[#8E9CB7]">
              Research Platform
            </span>
          </div>
        </div>

        <p className="mb-3 px-2 text-[11px] font-semibold uppercase tracking-wider text-[#566680]">
          Main Menu
        </p>
        <nav className="flex flex-col gap-1.5">
          {mainNav.map(({ label, icon: Icon, href, disabled }) => {
            const active = href !== "#" && (href === "/" ? pathname === "/" : pathname.startsWith(href));
            const isScreenersMain = href === "/screening";
            const isScreenerSubActive = pathname === "/screening" || pathname === "/technical" || pathname === "/momentum";
            const showScreenerSub = isScreenersMain || isScreenerSubActive;

            return (
              <div key={label}>
                <Link
                  href={href}
                  aria-disabled={disabled}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                    (active || (isScreenersMain && isScreenerSubActive))
                      ? "bg-[#10161A] text-[#DAE1EE] shadow-md shadow-[#10161A]/15"
                      : disabled
                        ? "cursor-not-allowed text-[#8E9CB7]/60"
                        : "text-[#566680] hover:bg-white/60 hover:text-[#10161A]"
                  }`}
                >
                  <Icon size={16} className={(active || (isScreenersMain && isScreenerSubActive)) ? "text-[#DAE1EE]" : "text-[#566680]"} />
                  <span>{label}</span>
                  {disabled && (
                    <span className="ml-auto rounded-md bg-[#B4C0D5]/40 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-[#566680]">
                      soon
                    </span>
                  )}
                </Link>
                {isScreenersMain && (
                  <div className="mt-1 ml-4 flex flex-col gap-1 border-l border-[#8E9CB7]/30 pl-3">
                    {screenerTypes.map(({ label: typeLabel, href: typeHref }) => {
                      const isActive = pathname === typeHref;
                      return (
                        <Link
                          key={typeLabel}
                          href={typeHref}
                          className={`text-xs font-medium rounded-lg px-2.5 py-2 transition-all ${
                            isActive
                              ? "bg-[#10161A]/60 text-[#DAE1EE]"
                              : "text-[#566680] hover:bg-white/40 hover:text-[#10161A]"
                          }`}
                        >
                          {typeLabel}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      <div>
        <div className="mb-4 rounded-xl border border-white/70 bg-white/50 p-3 backdrop-blur-md">
          <p className="text-[11px] font-semibold text-[#10161A]">PSX Pilot Environment</p>
          <p className="text-[10px] text-[#566680] leading-tight mt-0.5">
            Fertilizer Sector Fundamental Data &amp; Research Index
          </p>
        </div>

        <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-[#566680]">
          Support &amp; Preferences
        </p>
        <nav className="flex flex-col gap-1">
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium text-[#566680] hover:bg-white/60 hover:text-[#10161A] transition-colors">
            <HelpCircle size={15} />
            Documentation
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium text-[#566680] hover:bg-white/60 hover:text-[#10161A] transition-colors">
            <Settings size={15} />
            Preferences
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium text-[#566680] hover:bg-white/60 hover:text-[#10161A] transition-colors">
            <LogOut size={15} />
            Sign Out
          </Link>
        </nav>
      </div>
    </aside>
  );
}
