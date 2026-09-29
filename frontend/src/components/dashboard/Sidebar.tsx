"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  SlidersHorizontal,
  GraduationCap,
  Bell,
  Settings,
  HelpCircle,
  LogOut,
  BarChart2,
  FileSearch,
  Briefcase,
} from "lucide-react";

const mainNav = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/" },
  { label: "Screener", icon: SlidersHorizontal, href: "/screener" },
  { label: "Ranking", icon: BarChart2, href: "/ranking" },
  { label: "Research Studio", icon: FileSearch, href: "/research" },
  { label: "Portfolio", icon: Briefcase, href: "/portfolio" },
  { label: "Academy", icon: GraduationCap, href: "#", disabled: true },
  { label: "Watchlists & Alerts", icon: Bell, href: "#", disabled: true },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col justify-between border-r border-border bg-sidebar px-5 py-6">
      <div>
        <div className="mb-8 flex items-center gap-2 px-1">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-accent">
            <BarChart2 size={18} />
          </span>
          <span className="text-lg font-semibold tracking-tight">
            PSX<span className="text-accent">Research</span>
          </span>
        </div>

        <p className="mb-3 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
          Main Menu
        </p>
        <nav className="flex flex-col gap-1">
          {mainNav.map(({ label, icon: Icon, href, disabled }) => {
            const active = href !== "#" && (href === "/" ? pathname === "/" : pathname.startsWith(href));
            return (
              <Link
                key={label}
                href={href}
                aria-disabled={disabled}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? "bg-accent text-white shadow-lg shadow-accent/20"
                    : disabled
                      ? "cursor-not-allowed text-muted/50"
                      : "text-muted hover:bg-surface hover:text-foreground"
                }`}
              >
                <Icon size={17} />
                <span>{label}</span>
                {disabled && (
                  <span className="ml-auto rounded-full bg-surface-alt px-1.5 py-0.5 text-[9px] font-medium text-muted">
                    soon
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div>
        <p className="mb-3 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
          Account
        </p>
        <nav className="flex flex-col gap-1">
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted hover:bg-surface hover:text-foreground">
            <HelpCircle size={17} />
            Help
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted hover:bg-surface hover:text-foreground">
            <Settings size={17} />
            Settings
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted hover:bg-surface hover:text-foreground">
            <LogOut size={17} />
            Log Out
          </Link>
        </nav>
      </div>
    </aside>
  );
}
