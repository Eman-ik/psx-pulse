"use client";

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
  MessageSquare,
  TrendingUp,
  Search,
} from "lucide-react";
import { NavigationItem } from "@/components/glass";
import clsx from "clsx";

const mainNav = [
  { label: "Dashboard", icon: BarChart2, href: "/" },
  { label: "Market Overview", icon: BarChart2, href: "/market" },
  { label: "Research Studio", icon: FileSearch, href: "/research" },
  { label: "Compare Companies", icon: BarChart2, href: "/compare" },
  { label: "Ask PSX Pulse", icon: MessageSquare, href: "/research-ask", disabled: true },
  { label: "Trade Planning", icon: TrendingUp, href: "/research?tab=trade" },
  { label: "Company Search", icon: Search, href: "/search", disabled: true },
  { label: "Screeners", icon: SlidersHorizontal, href: "/screener" },
  { label: "Academy", icon: GraduationCap, href: "#", disabled: true },
  { label: "Watchlists & Alerts", icon: Bell, href: "#", disabled: true },
];

const screenerTypes = [
  { label: "Fundamental Screening", href: "/screening" },
  { label: "Technical Analysis", href: "/technical" },
  { label: "Momentum Analysis", href: "/momentum" },
];

const supportNav = [
  { label: "Preferences", icon: Settings, href: "#", disabled: true },
  { label: "Documentation", icon: HelpCircle, href: "#", disabled: true },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "#") return false;
    return href === "/" ? pathname === "/" : pathname.startsWith(href);
  };

  const isScreenerSubActive =
    pathname === "/screening" || pathname === "/technical" || pathname === "/momentum";

  return (
    <aside className={clsx(
      "hidden lg:flex w-64 shrink-0 flex-col justify-between",
      "glass-strong rounded-2xl m-4 p-6",
      "border border-[rgba(255,255,255,0.72)]"
    )}>
      {/* Logo & Branding */}
      <div>
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#10161A] text-white shadow-md">
            <BarChart2 size={18} />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold text-[#10161A]">
              PSX<span className="text-[#566680] font-medium ml-1">Pulse</span>
            </span>
            <span className="text-[9px] uppercase font-semibold tracking-wider text-[#8E9CB7]">
              Research
            </span>
          </div>
        </div>

        {/* Main Navigation */}
        <p className="mb-4 px-3 text-[10px] font-semibold uppercase tracking-wider text-[#566680]">
          Menu
        </p>
        <nav className="flex flex-col gap-1">
          {mainNav.map(({ label, icon: Icon, href, disabled }) => {
            const active = isActive(href);
            const isScreenersMain = href === "/screener";
            const showScreenerSub = isScreenersMain || isScreenerSubActive;

            return (
              <div key={label}>
                <NavigationItem
                  href={href}
                  label={label}
                  icon={<Icon size={16} />}
                  isActive={active || (isScreenersMain && isScreenerSubActive)}
                  badge={disabled ? "soon" : undefined}
                  disabled={disabled}
                />

                {/* Screener Submenu */}
                {showScreenerSub && (
                  <div className="mt-2 ml-4 flex flex-col gap-1 border-l border-[#8E9CB7]/30 pl-3">
                    {screenerTypes.map(({ label: typeLabel, href: typeHref }) => (
                      <NavigationItem
                        key={typeLabel}
                        href={typeHref}
                        label={typeLabel}
                        isActive={pathname === typeHref}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Environment & Support */}
      <div>
        {/* Environment Badge */}
        <div className="mb-6 rounded-xl border border-[rgba(255,255,255,0.58)] bg-[rgba(180,192,213,0.34)] p-3 backdrop-blur-lg">
          <p className="text-[10px] font-semibold uppercase text-[#10161A]">
            PSX Pilot
          </p>
          <p className="text-[10px] text-[#566680] leading-snug mt-1">
            Fertilizer Sector Data
          </p>
        </div>

        {/* Support Navigation */}
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-[#566680]">
          Support
        </p>
        <nav className="flex flex-col gap-1">
          {supportNav.map(({ label, icon: Icon, href }) => (
            <NavigationItem
              key={label}
              href={href}
              label={label}
              icon={<Icon size={15} />}
            />
          ))}
        </nav>
      </div>
    </aside>
  );
}
